cmake_minimum_required(VERSION 3.1...3.21)
project(
  foam
  VERSION 0.1
  LANGUAGES C CXX
)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_DEBUG "-g ${CMAKE_CXX_FLAGS_DEBUG}")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -flto ${CMAKE_CXX_FLAGS_RELEASE}")
set(CMAKE_CXX_FLAGS "-march=native ${CMAKE_CXX_FLAGS}")

set(CMAKE_C_FLAGS_DEBUG "-g ${CMAKE_C_FLAGS_DEBUG}")
set(CMAKE_C_FLAGS_RELEASE "-O3 -flto ${CMAKE_C_FLAGS_RELEASE}")
set(CMAKE_C_FLAGS "-march=native ${CMAKE_C_FLAGS}")

set(SRC_FILES
     src/src/API/DomainSampler.cpp
     src/src/API/Hybrid.cpp
     src/src/API/MergeHubbard.cpp
     src/src/API/MSBase.cpp
     src/src/API/MSGrid.cpp
     src/src/API/MSRelaxation.cpp
     src/src/API/REBase.cpp
     src/src/API/REDiscard.cpp
     src/src/API/RELargest.cpp
     src/src/API/RELargestLM.cpp
     src/src/API/REMaxElim.cpp
     src/src/API/RESelect.cpp
     src/src/API/SEConvex.cpp
     src/src/API/SEPoint.cpp
     src/src/API/SESphPt.cpp
     src/src/API/SFBase.cpp
     src/src/API/SFMinErr.cpp
     src/src/API/SFRitter.cpp
     src/src/API/SFWhite/ball.cpp
     src/src/API/SFWhite/complex.c
     src/src/API/SFWhite.cpp
     src/src/API/SFWhite/nrutil.c
     src/src/API/SFWhite/svd.cpp
     src/src/API/SOBalance.cpp
     src/src/API/SOBase.cpp
     src/src/API/SOPerSphere.cpp
     src/src/API/SOSimplex.cpp
     src/src/API/SRBurst.cpp
     src/src/API/SRComposite.cpp
     src/src/API/SRExpand.cpp
     src/src/API/SRGrid.cpp
     src/src/API/SRMerge.cpp
     src/src/API/SRQuickBurst.cpp
     src/src/API/SRSpawn.cpp
     src/src/API/SRStandOff.cpp
     src/src/API/SRVoronoi.cpp
     src/src/API/SSIsohedron.cpp
     src/src/API/SSRings.cpp
     src/src/API/STGGeneric.cpp
     src/src/API/STGHubbard.cpp
     src/src/API/STGOctree.cpp
     src/src/API/SurfaceDiv.cpp
     src/src/API/VFAdaptive.cpp
     src/src/API/VFGapCross.cpp
     src/src/Base/ProcMon.cpp
     src/src/BBox/BBox.cpp
     src/src/BBox/eigen.cpp
     src/src/BBox/MVBB/gdiam.cpp
     src/src/BBox/qHull/geom2.cpp
     src/src/BBox/qHull/geom.cpp
     src/src/BBox/qHull/global.cpp
     src/src/BBox/qHull/mem.cpp
     src/src/BBox/qHull/merge.cpp
     src/src/BBox/qHull/poly2.cpp
     src/src/BBox/qHull/poly.cpp
     src/src/BBox/qHull/qhull.cpp
     src/src/BBox/qHull/set.cpp
     src/src/BBox/qHull/stat.cpp
     src/src/BBox/qHull/user.cpp
     src/src/DecodeParam.cpp
     src/src/EvalTree.cpp
     src/src/Exceptions/ErrorLog.cpp
     src/src/Exceptions/Exception.cpp
     src/src/Exceptions/MemoryException.cpp
     src/src/Export/POV.cpp
     src/src/Export/VRML.cpp
     src/src/Geometry/Circle.cpp
     src/src/Geometry/CubeTri.cpp
     src/src/Geometry/Line2D.cpp
     src/src/Geometry/LineSeg.cpp
     src/src/Geometry/pcube/fpcube.cpp
     src/src/Geometry/pcube/pcube.cpp
     src/src/Geometry/Plane.cpp
     src/src/Geometry/Point2D.cpp
     src/src/Geometry/Point3D.cpp
     src/src/Geometry/RayBox.c
     src/src/Geometry/Ray.cpp
     src/src/Geometry/Sphere.cpp
     src/src/Geometry/Transform2D.cpp
     src/src/Geometry/Transform3D.cpp
     src/src/Geometry/TriTri.cpp
     src/src/Geometry/Vector2D.cpp
     src/src/Geometry/Vector3D.cpp
     src/src/LinearAlgebra/Matrix.cpp
     src/src/MedialAxis/Clusters.cpp
     src/src/MedialAxis/MedialTester.cpp
     src/src/MedialAxis/Voronoi3D.cpp
     src/src/MedialAxis/VoronoiFace.cpp
     src/src/MinMax/Simplex.cpp
     src/src/null.c
     src/src/SphereTree/SphereTree.cpp
     src/src/Surface/Internal.cpp
     src/src/Surface/InternalGem.cpp
     src/src/Surface/OBJLoader.cpp
     src/src/Surface/SpacialHash.cpp
     src/src/Surface/Surface.cpp
     src/src/Surface/SurfaceRep.cpp
     src/src/Surface/SurfaceTester.cpp
     src/src/Surface/VolInt.cpp
     src/src/Surface/Voxel.cpp
     src/src/VerifyModel.cpp
 )

add_library(spheretree STATIC ${SRC_FILES})

add_executable(makeTreeMedial src/src/makeTreeMedial.cpp)
# add_executable(makeTreeGrid src/makeTreeGrid.cpp)
# add_executable(makeTreeHubbard src/makeTreeHubbard.cpp)
# add_executable(makeTreeOctree src/makeTreeOctree.cpp)
# add_executable(makeTreeSpawn src/makeTreeSpawn.cpp)

target_link_libraries(makeTreeMedial PUBLIC spheretree)
# target_link_libraries(makeTreeGrid PUBLIC spheretree)
# target_link_libraries(makeTreeHubbard PUBLIC spheretree)
# target_link_libraries(makeTreeOctree PUBLIC spheretree)
# target_link_libraries(makeTreeSpawn PUBLIC spheretree)

add_custom_command(TARGET makeTreeMedial POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
    $<TARGET_FILE:makeTreeMedial>
    ${CMAKE_SOURCE_DIR}/foam/
    COMMENT "Copying 'makeTreeMedial' script to '${CMAKE_SOURCE_DIR}/foam/'")
