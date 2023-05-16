# Foam: Spherical Approximations of URDFs

## Obtaining & Building
```sh
git clone --recursive git@github.com:zkingston/foam.git
cd foam
cmake -Bbuild -GNinja .
cmake --build build/
```

## Third-party Dependencies
### [SphereTree](https://github.com/mlund/spheretree)
The code in the `./spheretree` directory has been copied from the linked directory and modified to build on modern systems with `CMake` rather than `autotools`.

### [ManifoldPlus](https://github.com/hjwdzh/ManifoldPlus/tree/master)
This code is included as a submodule.
