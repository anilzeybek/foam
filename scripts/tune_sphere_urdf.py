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
from grapeshot.model.simulator import contact_to_key
from grapeshot.util.constants import ALL_NO_BASE_GROUP
from grapeshot.simulators.pybullet import PyBulletSimulator
from grapeshot.util.filesystem import tempfile
from grapeshot.model.robot import process_srdf
from grapeshot.util.random import RNG


def evaluate_urdf(old_urdf: Path, urdf_str: str, seed: int = 0, samples: int = 1000) -> float:
    # TODO: set seed on RNG

    print("Evaluating URDF")
    exact_world = World(PyBulletSimulator(False))
    exact_skel = exact_world.add_skeleton(old_urdf)
    exact_groups = process_srdf(exact_skel, old_urdf.parent / (old_urdf.stem + ".srdf"))

    sphere_world = World(PyBulletSimulator(True))
    with tempfile(old_urdf.parent, extension = "urdf") as (f, path):
        f.write(urdf_str)
        f.flush()
        sphere_skel = sphere_world.add_skeleton(path)
        _ = process_srdf(sphere_skel, old_urdf.parent / (old_urdf.stem + ".srdf"))

    exact_world.setup_collision_filter()
    sphere_world.setup_collision_filter()

    group = exact_groups[ALL_NO_BASE_GROUP]

    values = []
    for i in range(samples):
        sample = group.sample_uniform()
        exact_world.set_group_positions(group, sample)
        sphere_world.set_group_positions(group, sample)

        distances = {}
        for contact in exact_world.get_closest_points():
            distances[contact_to_key(contact)] = contact.distance

        for contact in sphere_world.get_closest_points():
            distances[contact_to_key(contact)] -= contact.distance

        value = np.linalg.norm(np.array(list(distances.values())))
        values.append(value)
        print(f"{i}: {value}")

    return np.quantile(np.array(values), 0.7)


def generate_spheres(
        mesh_filename: Path,
        scale: NDArray | None,
        position: NDArray | None,
        orientation: NDArray | None,
        depth: int = 1,
        branch: int = 8,
        manifold_leaves: int = 1000,
        simplify_ratio: float = 0.2
    ) -> Spherization:
    loaded_mesh = load_mesh_file(mesh_filename)

    spheres = spherize_mesh(
        loaded_mesh,
        scale,
        position,
        orientation,
        {
            'depth': depth,
            'branch': branch,
            },
        {
            'manifold_leaves': manifold_leaves,
            'ratio': simplify_ratio,
            },
        )

    return spheres[-1]


class URDFSpherizer:

    def __init__(self, filename: Path, n_spheres: int = 64, sphere_threads: int = 4):
        self.filename = filename
        self.path = filename.parent
        self.sphere_threads = sphere_threads
        self.n_spheres = n_spheres
        with open(filename, 'r') as f:
            self.urdf = xmltodict.parse(f.read())

        self.cache = {}

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

    def train(self, config: Configuration, seed: int = 0) -> float:
        weights = {}
        for link in self.urdf['robot']['link']:
            if 'collision' not in link:
                continue

            name = link['@name']
            weights[name] = config[name]

        s = sum(weights.values())
        for k, v in weights.items():
            weights[k] = int(v / s * self.n_spheres)

        urdf = self.sphereize_urdf(weights)
        return evaluate_urdf(self.filename, urdf)

    def sphereize_urdf(self, allocation: dict[str, int]) -> str:
        meshes = {}
        for link in self.urdf['robot']['link']:
            if 'collision' not in link:
                continue

            name = link['@name']
            collision = link['collision']  # TODO: Assumes one collision geometry right now
            geometry = collision['geometry']

            position = None
            orientation = None
            if 'origin' in collision:
                position = np.fromiter(map(float, collision['origin']['@xyz'].split()), dtype = float)
                orientation = np.fromiter(map(float, collision['origin']['@rpy'].split()), dtype = float)

            if 'mesh' in geometry:
                mesh = geometry['mesh']
                mesh_filename = mesh['@filename']

                if mesh_filename.startswith('package://'):
                    mesh_filename = mesh_filename[len('package://'):]

                scale = np.array(mesh['@scale']) if 'scale' in mesh else None
                meshes[name] = (mesh_filename, scale, position, orientation)

        executor = ThreadPoolExecutor(max_workers = self.sphere_threads)
        link_to_futures = {}

        print(f"Computing spherization for {len(meshes)} meshes...")
        for link, (mesh, scale, position, orientation) in meshes.items():
            if (link, allocation[link]) in self.cache:
                continue

            link_to_futures[link] = executor.submit(
                generate_spheres, self.path / mesh, scale, position, orientation, allocation[link], 1, 1000
                )

        wait(link_to_futures.values())

        sphere_urdf = deepcopy(self.urdf)
        for link in sphere_urdf['robot']['link']:
            if 'collision' not in link:
                continue

            name = link['@name']

            collision = link['collision']  # TODO: Assumes one collision geometry right now
            geometry = collision['geometry']
            if 'mesh' in geometry:
                mesh = geometry['mesh']
                mesh_filename = mesh['@filename']
                if mesh_filename.startswith('package://'):
                    mesh_filename = mesh_filename[len('package://'):]

                collision = []
                if (name, allocation[name]) in self.cache:
                    spherization = self.cache[(name, allocation[name])]
                else:
                    spherization = link_to_futures[name].result()
                    self.cache[(name, allocation[name])] = spherization

                for sphere in spherization.spheres:
                    collision.append(
                        {
                            'geometry': {
                                'sphere': {
                                    '@radius': sphere.radius
                                    }
                                },
                            'origin': {
                                '@xyz': ' '.join(map(str, sphere.origin)), '@rpy': '0 0 0'
                                }
                            }
                        )
                    link['collision'] = collision

        return xmltodict.unparse(sphere_urdf, pretty = True)


def main(
        filename: str = "assets/panda/panda.urdf",
        depth: int = 1,
        maximum_spheres: int = 128,
        n_trials: int = 100,
        manifold_leaves: int = 1000,
        threads: int = 8
    ):
    filepath = Path(filename)

    model = URDFSpherizer(filepath)

    # Scenario object specifying the optimization "environment"
    scenario = Scenario(model.configspace, deterministic = True, n_trials = 100)

    # Now we use SMAC to find the best hyperparameters
    smac = HPOFacade(
        scenario,
        model.train,   # We pass the target function here
        overwrite =
        True,          # Overrides any previous results that are found that are inconsistent with the meta-data
        )

    incumbent = smac.optimize()


if __name__ == "__main__":
    Fire(main)
