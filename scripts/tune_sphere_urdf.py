from copy import deepcopy
from pathlib import Path

import numpy as np
import xmltodict
from ConfigSpace import Configuration, ConfigurationSpace, Integer
from fire import Fire
from grapeshot.model.robot import process_srdf
from grapeshot.model.world import World
from grapeshot.simulators.pybullet import PyBulletSimulator
from grapeshot.util.constants import ALL_NO_BASE_GROUP
from grapeshot.util.filesystem import tempfile
from grapeshot.util.random import set_RNG_seed
from smac import HyperparameterOptimizationFacade, Scenario

from foam import *


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
        self.ps = ParallelSpherizer(sphere_threads)
        self.db = SpherizationDatabase(Path(database))

        self.world = World(PyBulletSimulator(False))
        self.skel = self.world.add_skeleton(self.filename)
        self.groups = process_srdf(self.skel, self.path / (self.filename.stem + ".srdf"))
        self.world.setup_collision_filter()
        self.group = self.groups[ALL_NO_BASE_GROUP]

        train_values = []
        self.samples = []
        for _ in range(n_samples):
            sample = self.group.sample_uniform()
            self.samples.append(sample)
            self.world.set_group_positions(self.group, sample)
            train_values.append(min(self.world.get_closest_points()).distance)
        self.train_values = np.array(train_values)

    def evaluate_urdf(self, urdf_str: str, seed: int = 0) -> float:
        set_RNG_seed(seed)

        sphere_world = World(PyBulletSimulator(False))
        with tempfile(self.path, extension = "urdf") as (f, path):
            f.write(urdf_str)
            f.flush()

            sphere_skel = sphere_world.add_skeleton(path)
            process_srdf(sphere_skel, self.path / (self.filename.stem + ".srdf"))

        sphere_world.setup_collision_filter()

        spheres = []
        for sample in self.samples:
            sphere_world.set_group_positions(self.group, sample)
            spheres.append(min(sphere_world.get_closest_points()).distance)

        norm = np.linalg.norm(self.train_values - np.array(spheres))
        return float(norm)

    @property
    def configspace(self) -> ConfigurationSpace:
        cs = ConfigurationSpace(seed = 0)
        parameters = []

        links = []
        for link in self.urdf['robot']['link']:
            if 'collision' not in link:
                continue

            name = link['@name']
            links.append(name)

        for name in links:
            parameters.append(Integer(f"{name}", (1, self.n_spheres - len(links) + 1), default = 8))

        cs.add_hyperparameters(parameters)
        return cs

    def configuration_to_nspheres(self, config: Configuration) -> dict[str, int]:
        # Uniform -> Exponential -> Dirichlet (uniform over simplex)
        weights = {}
        for link in self.urdf['robot']['link']:
            if 'collision' not in link:
                continue

            name = link['@name']
            weights[name] = np.log(config[name] / 64.) / -len(config)

        s = sum(weights.values())
        for k, v in weights.items():
            v = int(round(v / s * self.n_spheres))
            weights[k] = max(v, 1)

        return weights

    def train(self, config: Configuration, seed: int = 0) -> float:
        weights = self.configuration_to_nspheres(config)

        print(f"Spherizing URDF")
        for k, v in weights.items():
            print(f"  {k}: {v}")
        urdf = self.sphereize_urdf(weights)
        value = self.evaluate_urdf(urdf, seed = seed)
        print(f"Evaluating URDF: {value}")
        return value

    def get_sphere_urdf(self, allocation: dict[str, int]) -> URDFDict:
        spheres = {}
        for mesh in self.meshes:
            branch = allocation[mesh.name]
            if not self.db.exists(mesh.name, branch, 1):
                spherization = self.ps.get(mesh.name)
                self.db.add(mesh.name, branch, 1, spherization[-1])
                spheres[mesh.name] = spherization[-1]

            else:
                spheres[mesh.name] = self.db.get(mesh.name, branch, 1)

        sphere_urdf = deepcopy(self.urdf)
        set_urdf_spheres(sphere_urdf, spheres)
        return sphere_urdf

    def sphereize_urdf(self, allocation: dict[str, int]) -> str:
        for mesh in self.meshes:
            branch = allocation[mesh.name]
            if not self.db.exists(mesh.name, branch, 1):
                self.ps.spherize_mesh(
                    mesh.name, mesh.filepath, mesh.scale, mesh.xyz, mesh.rpy, {
                        'depth': 1, 'branch': branch
                        }
                    )

        self.ps.wait()

        sphere_urdf = self.get_sphere_urdf(allocation)
        return xmltodict.unparse(sphere_urdf)


def main(
        filename: str = "assets/panda/panda.urdf",
        database: str = "sphere_database.json",
        output: str = "spherized.urdf",
        n_spheres: int = 64,
        n_trials: int = 100,
        threads: int = 8
    ):
    filepath = Path(filename)

    model = URDFSpherizer(filepath, n_spheres = n_spheres, sphere_threads = threads, database = database)
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
