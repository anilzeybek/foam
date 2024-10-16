import numpy as np
from foam import *

from fire import Fire

SPHERES = [
    (0.08, {
        "panda_link0": np.array([[0.0, 0.0, 0.05]])
        }),
    (
        0.06,
        {
            "panda_link1":
            np.array([
                [0.0, -0.08, 0.0],
                [0.0, -0.03, 0.0],
                [0.0, 0.0, -0.12],
                [0.0, 0.0, -0.17],
                ]),
            "panda_link2":
            np.array([
                [0.0, 0.0, 0.03],
                [0.0, 0.0, 0.08],
                [0.0, -0.12, 0.0],
                [0.0, -0.17, 0.0],
                ]),
            "panda_link3":
            np.array([[0.0, 0.0, -0.1]]),
            "panda_link4":
            np.array([[-0.08, 0.095, 0.0]]),
            "panda_link5":
            np.array([
                [0.0, 0.055, 0.0],
                [0.0, 0.075, 0.0],
                [0.0, 0.0, -0.22],
                ]),
            },
        ),
    (
        0.05,
        {
            "panda_link3": np.array([[0.0, 0.0, -0.06]]),
            "panda_link5": np.array([[0.0, 0.05, -0.18]]),
            "panda_link6": np.array([[0.0, 0.0, 0.0], [0.08, -0.01, 0.0]]),
            "panda_link7": np.array([[0.0, 0.0, 0.07]]),
            },
        ),
    (
        0.055,
        {
            "panda_link3": np.array([[0.08, 0.06, 0.0], [0.08, 0.02, 0.0]]),
            "panda_link4": np.array([
                [0.0, 0.0, 0.02],
                [0.0, 0.0, 0.06],
                [-0.08, 0.06, 0.0],
                ]),
            },
        ),
    (
        0.025,
        {
            "panda_link5":
            np.array(
                [
                    [0.01, 0.08, -0.14],
                    [0.01, 0.085, -0.11],
                    [0.01, 0.09, -0.08],
                    [0.01, 0.095, -0.05],
                    [-0.01, 0.08, -0.14],
                    [-0.01, 0.085, -0.11],
                    [-0.01, 0.09, -0.08],
                    [-0.01, 0.095, -0.05],
                    ]
                ),
            "panda_link7":
            np.array([[0.02, 0.04, 0.08], [0.04, 0.02, 0.08]]),
            },
        ),
    (0.052, {
        "panda_link6": np.array([[0.08, 0.035, 0.0]])
        }),
    (0.02, {
        "panda_link7": np.array([[0.04, 0.06, 0.085], [0.06, 0.04, 0.085]])
        }),
    (
        0.028,
        {
            "panda_hand":
            np.array(
                [
                    [0.0, -0.075, 0.01],
                    [0.0, -0.045, 0.01],
                    [0.0, -0.015, 0.01],
                    [0.0, 0.015, 0.01],
                    [0.0, 0.045, 0.01],
                    [0.0, 0.075, 0.01],
                    ]
                )
            },
        ),
    (
        0.026,
        {
            "panda_hand":
            np.array(
                [
                    [0.0, -0.075, 0.03],
                    [0.0, -0.045, 0.03],
                    [0.0, -0.015, 0.03],
                    [0.0, 0.015, 0.03],
                    [0.0, 0.045, 0.03],
                    [0.0, 0.075, 0.03],
                    ]
                )
            },
        ),
    (
        0.024,
        {
            "panda_hand":
            np.array(
                [
                    [0.0, -0.075, 0.05],
                    [0.0, -0.045, 0.05],
                    [0.0, -0.015, 0.05],
                    [0.0, 0.015, 0.05],
                    [0.0, 0.045, 0.05],
                    [0.0, 0.075, 0.05],
                    ]
                )
            },
        ),
    (
        0.012,
        {
            "panda_leftfinger": np.array([
                [0, 0.015, 0.022],
                [0, 0.008, 0.044],
                ]),
            "panda_rightfinger": np.array([
                [0, -0.015, 0.022],
                [0, -0.008, 0.044],
                ]),
            },
        ),
    ]


def spheres_to_spherization(meshin):
    meshes = {i.name: Spherization([], 0, 0, 0) for i in meshin}
    for radius, s in SPHERES:
        for k, v in s.items():
            for vv in v[:]:
                meshes[k].spheres.append(Sphere(*list(vv), radius))

    return meshes


def main(
    filename: str = "assets/panda/panda.urdf",
    output: str = "spherized.urdf",
    ):
    urdf = load_urdf(Path(filename))
    meshes = get_urdf_meshes(urdf)
    set_urdf_spheres(urdf, spheres_to_spherization(meshes))
    save_urdf(urdf, Path(output))


if __name__ == "__main__":
    Fire(main)
