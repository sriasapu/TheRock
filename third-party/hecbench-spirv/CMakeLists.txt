# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

therock_subproject_fetch(therock-hecbench-sources
  CMAKE_PROJECT
  # TODO: Upload to S3 mirror and restore the S3 URL before merging.
  URL https://github.com/zjin-lcf/HeCBench/archive/a2efabf38919f26c0c607e22e84cd2b7dde911a1.tar.gz
  URL_HASH SHA256=787732c67ec0adfe702c88da6278b655635f752707cfcbc99097d472eb8b81fa
)

# Build complete CFLAGS with prim includes from BUILD_DEPS
set(_hecbench_cflags "-x hip --offload-arch=amdgcnspirv -std=c++17 -Wall")
string(APPEND _hecbench_cflags " -I${THEROCK_BINARY_DIR}/math-libs/hipCUB/stage/include")
string(APPEND _hecbench_cflags " -I${THEROCK_BINARY_DIR}/math-libs/rocPRIM/stage/include")

therock_cmake_subproject_declare(hecbench-spirv
  EXTERNAL_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/project"
  BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/hecbench-spirv"
  BACKGROUND_BUILD
  EXCLUDE_FROM_ALL
  NO_MERGE_COMPILE_COMMANDS
  OUTPUT_ON_FAILURE
  EXTRA_DEPENDS
    therock-hecbench-sources
  CMAKE_ARGS
    "-DHECBENCH_SOURCE_DIR=${CMAKE_CURRENT_BINARY_DIR}/source"
    "-DHECBENCH_SPIRV_CFLAGS=${_hecbench_cflags}"
  BUILD_DEPS
    hipCUB
    rocPRIM
  RUNTIME_DEPS
    hip-clr
  COMPILER_TOOLCHAIN
    amd-hip
)
therock_cmake_subproject_activate(hecbench-spirv)

therock_provide_artifact(hecbench-spirv
  DESCRIPTOR artifact-hecbench-spirv.toml
  COMPONENTS
    lib
    test
  SUBPROJECT_DEPS
    hecbench-spirv
)
