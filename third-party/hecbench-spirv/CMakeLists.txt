# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

therock_subproject_fetch(therock-hecbench-sources
  CMAKE_PROJECT
  # Originally mirrored from: https://github.com/zjin-lcf/HeCBench/archive/a2efabf38919f26c0c607e22e84cd2b7dde911a1.tar.gz
  URL https://rocm-third-party-deps.s3.us-east-2.amazonaws.com/hecbench-a2efabf38919f26c0c607e22e84cd2b7dde911a1.tar.gz
  URL_HASH SHA256=787732c67ec0adfe702c88da6278b655635f752707cfcbc99097d472eb8b81fa
)

therock_cmake_subproject_declare(hecbench-spirv
  EXTERNAL_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/project"
  BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/hecbench-spirv"
  BACKGROUND_BUILD
  CMAKE_ARGS
    "-DHECBENCH_SOURCE_DIR=${CMAKE_CURRENT_BINARY_DIR}/source"
    "-DTHEROCK_ROCM_PATH_HINT=${STAGING_INSTALL_DIR}"
    "-DTHEROCK_CXX_COMPILER_HINT=${CMAKE_CXX_COMPILER}"
    "-DTHEROCK_HIPCC_HINT=${CMAKE_HIP_COMPILER}"
  COMPILER_TOOLCHAIN
    amd-hip
  BUILD_DEPS
    therock-hecbench-sources
    hip-clr
    amd-llvm
)
therock_cmake_subproject_activate(hecbench-spirv)

therock_provide_artifact(hecbench-spirv
  TARGET_NEUTRAL
  DESCRIPTOR artifact-hecbench-spirv.toml
  COMPONENTS
    lib
    test
  SUBPROJECT_DEPS
    hecbench-spirv
)


