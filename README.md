# Foam: Spherical Approximations of URDFs

## Obtaining & Building
```sh
git clone --recursive git@github.com:zkingston/foam.git
cd foam
cmake -Bbuild -GNinja .
cmake --build build/
```

## Scripts

:warning: HEAVY WIP :warning:
In the `scripts` directory:

- `python generate_spheres.py <mesh>`: creates spheres.
  Optionally specify `--depth <depth>` and `--branch <branching factor>` to control sphere generation process.
  Can also specify `--manifold-leaves <leaves>` to control mesh correction on invalid meshes.
- `python visualize_spheres.py <mesh> <spheres>`: visualizes spheres and mesh.
  Optionally specify `--depth <depth>` for the sphere level to visualize.

## Third-party Dependencies

Third-party dependencies are stored in the `./external` directory.
Compiled script binaries are copied into the `foam/external` directory.

### [SphereTree](https://github.com/mlund/spheretree)
The code in the `./spheretree` directory has been copied from the linked directory and modified to build on modern systems with `CMake` rather than `autotools`.

### [Manifold](https://github.com/hjwdzh/Manifold)
This code is included as a submodule.

### [ManifoldPlus](https://github.com/hjwdzh/ManifoldPlus)
This code is included as a submodule.

### [Quadric Mesh Simplification](https://github.com/sp4cerat/Fast-Quadric-Mesh-Simplification)
This code is included as a submodule.
