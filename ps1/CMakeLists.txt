cmake_minimum_required(VERSION 3.21)

project(funkin_ps1_probe LANGUAGES C CXX ASM VERSION 0.1.0)

psn00bsdk_add_executable(funkin-ps1-probe GPREL main.c)

psn00bsdk_add_cd_image(
	ps1-disc
	funkin-ps1-probe
	iso.xml
	DEPENDS funkin-ps1-probe system.cnf
)

# Optional CD-audio clock probe. This uses a generated, rights-safe click track
# while official stems remain local-only until their distribution terms and
# input files are available.
if(DEFINED FUNKIN_PS1_AUDIO_WAV AND EXISTS "${FUNKIN_PS1_AUDIO_WAV}")
	configure_file("${FUNKIN_PS1_AUDIO_WAV}" "${CMAKE_CURRENT_BINARY_DIR}/audio-probe.wav" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-audio-probe GPREL audio_probe.c)
	psn00bsdk_add_cd_image(
		ps1-audio-disc
		funkin-ps1-audio-probe
		audio_iso.xml
		DEPENDS funkin-ps1-audio-probe system.cnf "${CMAKE_CURRENT_BINARY_DIR}/audio-probe.wav"
	)
elseif(DEFINED FUNKIN_PS1_AUDIO_WAV)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_WAV does not name an existing PCM WAV file")
endif()

# Optional PSn00bSDK CD-to-SPU ADPCM streaming probe. The SDK's reusable
# streaming implementation remains in the external SDK installation.
if(DEFINED FUNKIN_PS1_AUDIO_VAGI AND EXISTS "${FUNKIN_PS1_AUDIO_VAGI}")
	get_filename_component(_psn00bsdk_lib_dir "$ENV{PSN00BSDK_LIBS}" DIRECTORY)
	get_filename_component(_psn00bsdk_root "${_psn00bsdk_lib_dir}" DIRECTORY)
	set(_psn00bsdk_cdstream_dir
		"${_psn00bsdk_root}/share/psn00bsdk/examples/sound/cdstream")
	if(NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.c" OR
	   NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.h")
		message(FATAL_ERROR
			"PSn00bSDK cdstream example sources were not found under ${_psn00bsdk_cdstream_dir}")
	endif()
	configure_file("${FUNKIN_PS1_AUDIO_VAGI}"
		"${CMAKE_CURRENT_BINARY_DIR}/stream.vag" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-spu-probe GPREL
		spu_probe.c
		"${_psn00bsdk_cdstream_dir}/stream.c")
	target_compile_definitions(funkin-ps1-spu-probe PRIVATE TEST_CHANNELS=2)
	target_include_directories(funkin-ps1-spu-probe PRIVATE
		"${_psn00bsdk_cdstream_dir}")
	psn00bsdk_add_cd_image(
		ps1-spu-disc
		funkin-ps1-spu-probe
		spu_iso.xml
		DEPENDS funkin-ps1-spu-probe system.cnf
			"${CMAKE_CURRENT_BINARY_DIR}/stream.vag"
	)
elseif(DEFINED FUNKIN_PS1_AUDIO_VAGI)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_VAGI does not name an existing VAGi file")
endif()

# Separate four-channel instrumental L/R + voice L/R stream probe. Keeping this
# as a distinct image preserves the stereo baseline and its fixture workflow.
if(DEFINED FUNKIN_PS1_AUDIO_VAGI_4CH AND EXISTS "${FUNKIN_PS1_AUDIO_VAGI_4CH}")
	get_filename_component(_psn00bsdk_lib_dir "$ENV{PSN00BSDK_LIBS}" DIRECTORY)
	get_filename_component(_psn00bsdk_root "${_psn00bsdk_lib_dir}" DIRECTORY)
	set(_psn00bsdk_cdstream_dir
		"${_psn00bsdk_root}/share/psn00bsdk/examples/sound/cdstream")
	if(NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.c" OR
	   NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.h")
		message(FATAL_ERROR
			"PSn00bSDK cdstream example sources were not found under ${_psn00bsdk_cdstream_dir}")
	endif()
	configure_file("${FUNKIN_PS1_AUDIO_VAGI_4CH}"
		"${CMAKE_CURRENT_BINARY_DIR}/stream-4ch.vag" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-spu-4ch-probe GPREL
		spu_probe.c
		"${_psn00bsdk_cdstream_dir}/stream.c")
	target_compile_definitions(funkin-ps1-spu-4ch-probe PRIVATE TEST_CHANNELS=4)
	target_include_directories(funkin-ps1-spu-4ch-probe PRIVATE
		"${_psn00bsdk_cdstream_dir}")
	psn00bsdk_add_cd_image(
		ps1-spu-4ch-disc
		funkin-ps1-spu-4ch-probe
		spu_4ch_iso.xml
		DEPENDS funkin-ps1-spu-4ch-probe system.cnf
			"${CMAKE_CURRENT_BINARY_DIR}/stream-4ch.vag"
	)
elseif(DEFINED FUNKIN_PS1_AUDIO_VAGI_4CH)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_VAGI_4CH does not name an existing VAGi file")
endif()

# Full-length classic Bopeebo playback check. Its source OGGs are decoded and
# encoded to a six-channel VAGi outside the repository; no game assets are
# copied into Git. Circle mutes BF's player-voice pair while Dad remains live.
if(DEFINED FUNKIN_PS1_AUDIO_VAGI_BOPEEBO AND EXISTS "${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO}")
	get_filename_component(_psn00bsdk_lib_dir "$ENV{PSN00BSDK_LIBS}" DIRECTORY)
	get_filename_component(_psn00bsdk_root "${_psn00bsdk_lib_dir}" DIRECTORY)
	set(_psn00bsdk_cdstream_dir
		"${_psn00bsdk_root}/share/psn00bsdk/examples/sound/cdstream")
	if(NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.c" OR
	   NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.h")
		message(FATAL_ERROR
			"PSn00bSDK cdstream example sources were not found under ${_psn00bsdk_cdstream_dir}")
	endif()
	configure_file("${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO}"
		"${CMAKE_CURRENT_BINARY_DIR}/bopeebo.vag" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-bopeebo-audio GPREL
		spu_probe.c
		"${_psn00bsdk_cdstream_dir}/stream.c")
	target_compile_definitions(funkin-ps1-bopeebo-audio PRIVATE
		TEST_CHANNELS=6
		TEST_NO_LOOP=1
		TEST_TOTAL_SAMPLES=1799280u)
	target_include_directories(funkin-ps1-bopeebo-audio PRIVATE
		"${_psn00bsdk_cdstream_dir}")
	psn00bsdk_add_cd_image(
		ps1-bopeebo-audio-disc
		funkin-ps1-bopeebo-audio
		bopeebo_audio_iso.xml
		DEPENDS funkin-ps1-bopeebo-audio system.cnf
			"${CMAKE_CURRENT_BINARY_DIR}/bopeebo.vag"
	)
elseif(DEFINED FUNKIN_PS1_AUDIO_VAGI_BOPEEBO)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_VAGI_BOPEEBO does not name an existing VAGi file")
endif()
