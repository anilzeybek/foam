from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, wait
from copy import deepcopy
from pathlib import Path
from typing import Any

import xmltodict
from fire import Fire
from foam import *
import numpy as np

from smac import HyperparameterOptimizationFacade as HPOFacade
from smac import RunHistory, Scenario
from ConfigSpace import Configuration, ConfigurationSpace, Float

from grapeshot.model.world import World
from grapeshot.util.constants import ALL_NO_BASE_GROUP
from grapeshot.simulators.pybullet import PyBulletSimulator
from grapeshot.util.filesystem import tempfile
from grapeshot.model.robot import process_srdf
from grapeshot.util.random import RNG


def evaluate_urdf(old_urdf: Path, urdf_str: str, seed: int = 0, samples: int = 100) -> float:
    # TODO: set seed on RNG
    exact_world = World(PyBulletSimulator(False))
    exact_skel = exact_world.add_skeleton(old_urdf)
    exact_groups = process_srdf(exact_skel, old_urdf.parent / (old_urdf.stem + ".srdf"))

    sphere_world = World(PyBulletSimulator(False))
    with tempfile(old_urdf.parent, extension = "urdf") as (f, path):
        f.write(urdf_str)
        f.flush()
        sphere_skel = sphere_world.add_skeleton(path)
        _ = process_srdf(sphere_skel, old_urdf.parent / (old_urdf.stem + ".srdf"))

    exact_world.setup_collision_filter()
    sphere_world.setup_collision_filter()

    group = exact_groups[ALL_NO_BASE_GROUP]

    exacts = []
    spheres = []
    for i in range(samples):
        sample = group.sample_uniform()
        exact_world.set_group_positions(group, sample)
        sphere_world.set_group_positions(group, sample)

        exacts.append(min(exact_world.get_closest_points()).distance)
        spheres.append(min(sphere_world.get_closest_points()).distance)

    norm = np.linalg.norm(np.array(exacts) - np.array(spheres))
    print(norm)
    return norm

class URDFSpherizer:

    def __init__(self, filename: Path, n_spheres: int = 64, sphere_threads: int = 4, database: str = "sphere_database.json"):
        self.filename = filename
        self.path = filename.parent
        self.n_spheres = n_spheres
        self.urdf = load_urdf(filename)
        self.meshes = get_urdf_meshes(self.urdf)
        self.ps = ParallelSpherizer(sphere_threads)
        self.db = SpherizationDatabase(Path(database))

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
            parameters.append(Float(f"{name}", (1. / len(links), 1), default = 1.))

        cs.add_hyperparameters(parameters)

        return cs

    def configuration_to_nspheres(self, config: Configuration) -> dict[str, int]:
        weights = {}
        for link in self.urdf['robot']['link']:
            if 'collision' not in link:
                continue

            name = link['@name']
            weights[name] = config[name]

        s = sum(weights.values())
        for k, v in weights.items():
            weights[k] = max(int(v / s * self.n_spheres), 1)

        return weights

    def train(self, config: Configuration, seed: int = 0) -> float:
        weights = self.configuration_to_nspheres(config)

        print(f"Spherizing URDF")
        for k, v in weights.items():
            print(f"  {k}: {v}")
        urdf = self.sphereize_urdf(weights)
        value = evaluate_urdf(self.filename, urdf)
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
                self.ps.spherize_mesh(mesh.name, mesh.filepath, mesh.scale, mesh.xyz, mesh.rpy,
                                 {'depth': 1, 'branch': branch})

        self.ps.wait()

        sphere_urdf = self.get_sphere_urdf(allocation)
        return xmltodict.unparse(sphere_urdf)

def main(
        filename: str = "assets/panda/panda.urdf",
        database: str = "sphere_database.json",
        output: str = "spherized.urdf",
        n_spheres: int = 128,
        n_trials: int = 100,
        threads: int = 8
    ):
    filepath = Path(filename)

    model = URDFSpherizer(filepath, n_spheres = n_spheres, sphere_threads = threads, database = database)

    scenario = Scenario(model.configspace, deterministic = True, n_trials = n_trials)

    smac = HPOFacade(
        scenario,
        model.train,
        overwrite = True
        )

    incumbent = smac.optimize()
    sphere_urdf = model.get_sphere_urdf(model.configuration_to_nspheres(incumbent))
    save_urdf(sphere_urdf, Path(output))

if __name__ == "__main__":
    Fire(main)
