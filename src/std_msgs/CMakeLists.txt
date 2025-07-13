cmake_minimum_required(VERSION 3.18)

project(std_msgs LANGUAGES CXX VERSION 1.0.0)

# ------------------------------------------------------------
# Compiler / dependencies
# ------------------------------------------------------------
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS  OFF)

add_compile_options(-Wall -Wextra -Wnon-virtual-dtor
                    -Wno-deprecated-declarations -Wno-unused-result)

find_package(Boost REQUIRED)
find_package(CycloneDDS REQUIRED COMPONENTS CXX)
find_package(CycloneDDS-CXX REQUIRED)

# ------------------------------------------------------------
# Output dirs
# ------------------------------------------------------------
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# ------------------------------------------------------------
# Collect *.idl (any depth)
# ------------------------------------------------------------
file(GLOB_RECURSE ORIGINAL_IDL_FILES "${CMAKE_CURRENT_SOURCE_DIR}/*.idl")

set(GENERATED_SRCS)
set(GENERATED_HDRS)
set(GENERATED_INCLUDE_DIRS)

# ------------------------------------------------------------
# Generate code
# ------------------------------------------------------------
foreach(IDL_FILE IN LISTS ORIGINAL_IDL_FILES)
    get_filename_component(IDL_DIR       "${IDL_FILE}" DIRECTORY)        # â¦/msg or â¦/srv
    get_filename_component(SUBDIR_NAME   "${IDL_DIR}"  NAME)            # msg|srv
    get_filename_component(PKG_DIR       "${IDL_DIR}"  DIRECTORY)       # â¦/<pkg>
    get_filename_component(PKG_NAME      "${PKG_DIR}"  NAME)
    get_filename_component(IDL_BASENAME  "${IDL_FILE}" NAME_WE)

    # output dir mirrors original layout
    set(GEN_DIR "${CMAKE_BINARY_DIR}/generated/${PKG_NAME}/${SUBDIR_NAME}")
    file(MAKE_DIRECTORY "${GEN_DIR}")

    set(GEN_CPP "${GEN_DIR}/${IDL_BASENAME}.cpp")
    set(GEN_HPP "${GEN_DIR}/${IDL_BASENAME}.hpp")

    # header search paths for idlc
    set(IDL_INC_ARGS
        -I "${PKG_DIR}/msg/"           # <pkg>/msg
        -I "${PKG_DIR}/srv/"           # <pkg>/srv
        -I "${PKG_DIR}/.."            # <pkg>/../
    )

    add_custom_command(
        OUTPUT "${GEN_CPP}" "${GEN_HPP}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${GEN_DIR}"
        COMMAND ${CMAKE_COMMAND} -E chdir "${GEN_DIR}"
                idlc -l cxx -fcase-sensitive
                    ${IDL_INC_ARGS}
                    "${IDL_FILE}"
        COMMAND sed -i "s|return \\\"${PKG_NAME}::${SUBDIR_NAME}::${IDL_BASENAME}\\\";|return \\\"${PKG_NAME}::${SUBDIR_NAME}::dds_::${IDL_BASENAME}_\\\";|g" "${GEN_HPP}"
        #COMMAND sed -i "s|return \\\"${PKG_NAME}::${SUBDIR_NAME}::${IDL_BASENAME}\\\";|return \\\"${PKG_NAME}/${SUBDIR_NAME}/${IDL_BASENAME}\\\";|g" "${GEN_HPP}"
        DEPENDS "${IDL_FILE}"
        COMMENT "Generating code and replacing text in ${GEN_HPP}"
        VERBATIM
    )

    list(APPEND GENERATED_SRCS  "${GEN_CPP}")
    list(APPEND GENERATED_HDRS  "${GEN_HPP}")
    list(APPEND GENERATED_INCLUDE_DIRS
         "${GEN_DIR}"                        # â¦/<pkg>/msg or srv
         "${CMAKE_BINARY_DIR}/generated/${PKG_NAME}")  # ããã±ã¼ã¸ã«ã¼ã
endforeach()

# ------------------------------------------------------------
# Build library
# ------------------------------------------------------------
add_library(std_msgs SHARED ${GENERATED_SRCS})
set_target_properties(std_msgs PROPERTIES LINKER_LANGUAGE CXX)

target_include_directories(std_msgs
    PUBLIC
        ${CMAKE_BINARY_DIR}/generated/
        $<BUILD_INTERFACE:${GENERATED_INCLUDE_DIRS}>
        $<INSTALL_INTERFACE:include>)

target_link_libraries(std_msgs
    PUBLIC CycloneDDS::ddsc CycloneDDS-CXX::ddscxx Boost::boost
    builtin_interfaces
    )

target_compile_definitions(std_msgs
    PUBLIC DDSCXX_NO_STD_OPTIONAL)

add_custom_target(std_msgs_generate
    DEPENDS ${GENERATED_SRCS} ${GENERATED_HDRS})
add_dependencies(std_msgs std_msgs_generate)

# ------------------------------------------------------------
# Install (headers only, preserve layout)
# ------------------------------------------------------------
install(TARGETS std_msgs
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
        RUNTIME DESTINATION bin)

install(DIRECTORY ${CMAKE_BINARY_DIR}/generated/
        DESTINATION include
        FILES_MATCHING PATTERN "*.hpp")

# make <pkg> root dirs visible to consumers
file(GLOB CHILD_PKG_DIRS LIST_DIRECTORIES TRUE
     "${CMAKE_BINARY_DIR}/generated/*")
foreach(PKG_DIR IN LISTS CHILD_PKG_DIRS)
    target_include_directories(std_msgs PUBLIC "${PKG_DIR}")
endforeach()
