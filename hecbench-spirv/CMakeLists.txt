# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

therock_cmake_subproject_declare(hecbench-spirv
  EXTERNAL_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/project"
  BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/hecbench-spirv"
  BACKGROUND_BUILD
  CMAKE_ARGS
    "-DTHEROCK_SOURCE_DIR=${THEROCK_SOURCE_DIR}"
    "-DTHEROCK_ROCM_PATH_HINT=${STAGING_INSTALL_DIR}"
    "-DTHEROCK_CXX_COMPILER_HINT=${CMAKE_CXX_COMPILER}"
    "-DTHEROCK_HIPCC_HINT=${CMAKE_HIP_COMPILER}"
  COMPILER_TOOLCHAIN
    amd-hip
  BUILD_DEPS
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
