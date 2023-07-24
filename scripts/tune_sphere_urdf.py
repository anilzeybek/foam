from copy import deepcopy
from pathlib import Path

import numpy as np
import xmltodict
from ConfigSpace import Configuration, ConfigurationSpace, Integer
from fire import Fire
from grapeshot.model.robot import process_srdf
from grapeshot.model.world import World
from grapeshot.model.environment import process_environment_yaml
from grapeshot.simulators.pybullet import PyBulletSimulator
from grapeshot.util.constants import ALL_NO_BASE_GROUP
from grapeshot.util.filesystem import tempfile
from grapeshot.util.random import set_RNG_seed
from smac import HyperparameterOptimizationFacade, Scenario

from foam import *


class GrapeshotHelper:

    def __init__(self, urdf: Path, srdf: Path, links: list[str]):
        self.world = World(PyBulletSimulator(False))
        self.skel = self.world.add_skeleton(urdf)
        _ = self.world.add_environment_builder(process_environment_yaml('./assets/spheres_scene.yaml'))

        self.groups = process_srdf(self.skel, srdf)
        self.group = self.groups[ALL_NO_BASE_GROUP]
        self.links = [self.skel.get_link(name) for name in links]

        self.world.setup_collision_filter()

    def sample(self) -> NDArray:
        return self.group.sample_uniform()

    def get_min_per_link(self, sample: NDArray) -> NDArray:
        self.world.set_group_positions(self.group, sample)

        distances = []
        for link in self.links:
            points = list(self.world.get_closest_points_to_link(link))
            distances.append(min(points).distance if points else 0.)

        return np.array(distances)


class URDFSpherizer:

    def __init__(
            self,
            filename: Path,
            n_spheres: int = 64,
            n_samples: int = 1000,
            sphere_threads: int = 4,
            database: str = "sphere_database.json"
        ):
        self.filename = filename
        self.path = filename.parent
        self.n_spheres = n_spheres
        self.urdf = load_urdf(filename)
        self.meshes = get_urdf_meshes(self.urdf)
        self.sh = SpherizationHelper(Path(database), sphere_threads)

        self.links = [link['@name'] for link in self.urdf['robot']['link'] if 'collision' in link]
        self.gs = GrapeshotHelper(self.filename, self.path / (self.filename.stem + ".srdf"), self.links)

        train_values = []
        self.samples = []
        for _ in range(n_samples):
            sample = self.gs.sample()
            self.samples.append(sample)
            train_values.append(self.gs.get_min_per_link(sample))

        self.train_values = np.concatenate(train_values)

    def evaluate_urdf(self, urdf_str: str, seed: int = 0) -> float:
        set_RNG_seed(seed)

        with tempfile(self.path, extension = "urdf") as (f, path):
            f.write(urdf_str)
            f.flush()
            sphere_gs = GrapeshotHelper(path, self.path / (self.filename.stem + ".srdf"), self.links)

        spheres = []
        for sample in self.samples:
            spheres.append(sphere_gs.get_min_per_link(sample))

        return float(np.linalg.norm(self.train_values - np.concatenate(spheres)))

    @property
    def configspace(self) -> ConfigurationSpace:
        cs = ConfigurationSpace(seed = 0)
        cs.add_hyperparameters(
            [
                Integer(f"{name}", (1, self.n_spheres - len(self.links) + 1), default = 8)
                for name in self.links
                ]
            )
        return cs

    def configuration_to_nspheres(self, config: Configuration) -> dict[str, int]:
        # Uniform -> Exponential -> Dirichlet (uniform over simplex)
        weights = {name: np.log(config[name] / 64.) / -len(config) for name in self.links}

        s = sum(weights.values())
        for k, v in weights.items():
            weights[k] = max(int(round(v / s * self.n_spheres)), 1)

        return weights

    def train(self, config: Configuration, seed: int = 0) -> float:
        weights = self.configuration_to_nspheres(config)

        for mesh in self.meshes:
            self.sh.spherize_mesh(
                mesh.name, mesh.filepath, mesh.scale, mesh.xyz, mesh.rpy, 1, weights[mesh.name]
                )

        sphere_urdf = self.get_sphere_urdf(weights)
        urdf = xmltodict.unparse(sphere_urdf)
        value = self.evaluate_urdf(urdf, seed = seed)

        print(f"Spherizing URDF")
        for k, v in weights.items():
            print(f"  {k}: {v}")
        print(f"Evaluating URDF: {value}")
        print()

        return value

    def get_sphere_urdf(self, allocation: dict[str, int]) -> URDFDict:
        spheres = {
            mesh.name: self.sh.get_spherization(mesh.name, 1, allocation[mesh.name])
            for mesh in self.meshes
            }
        sphere_urdf = deepcopy(self.urdf)
        set_urdf_spheres(sphere_urdf, spheres)
        return sphere_urdf


def main(
        filename: str = "assets/panda/panda.urdf",
        database: str = "sphere_database.json",
        output: str = "spherized.urdf",
        n_spheres: int = 50,
        n_trials: int = 1000,
        n_samples: int = 1000,
        threads: int = 8
    ):
    filepath = Path(filename)

    model = URDFSpherizer(filepath, n_spheres = n_spheres, n_samples=n_samples, sphere_threads = threads, database = database)
    scenario = Scenario(model.configspace, n_trials = n_trials, deterministic = True)
    smac = HyperparameterOptimizationFacade(scenario, model.train, overwrite = True)
    incumbent = smac.optimize()

    allocation = model.configuration_to_nspheres(incumbent)
    print("Final Spherization:")
    for k, v in allocation.items():
        print(f"  {k}: {v}")

    sphere_urdf = model.get_sphere_urdf(allocation)
    save_urdf(sphere_urdf, Path(output))


if __name__ == "__main__":
    Fire(main)
