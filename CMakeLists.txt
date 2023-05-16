cmake_minimum_required(VERSION 3.1...3.21)
project(
  foam
  VERSION 0.1
  LANGUAGES C CXX
)

add_subdirectory(spheretree)
add_subdirectory(manifold)
