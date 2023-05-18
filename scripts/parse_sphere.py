import trimesh as t
from trimesh.viewer import SceneViewer

with open('test.sph', 'r') as f:
    lines = f.readlines()
    n_sphere = lines.index('\n')
    spheres = [
        list(map(float, line.split()))[:-1]
        for line in lines[1+1:1+1+8]
    ]

    mesh = t.load_mesh('link0.obj')
    scene = t.Scene([mesh])
    for sphere in spheres:
        print(sphere)
        tf = t.transformations.translation_matrix(sphere[:3])
        scene.add_geometry(t.creation.icosphere(radius=sphere[-1]),
                           transform=tf)

    SceneViewer(scene)
