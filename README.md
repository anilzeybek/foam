# Foam: Spherical Approximations of URDFs

## Obtaining & Building
```sh
git clone git@github.com:zkingston/foam.git
cd foam
cmake -Bbuild -GNinja .
cmake --build build/
```

## Scripts

:warning: HEAVY WIP :warning:
In the `scripts` directory:

- `python spheres.py <mesh>`: creates spheres
- `python visualize.py --mesh <mesh> --spheres <spheres>`: visualizes spheres and mesh

## Third-party Dependencies
### [SphereTree](https://github.com/mlund/spheretree)
The code in the `./spheretree` directory has been copied from the linked directory and modified to build on modern systems with `CMake` rather than `autotools`.
