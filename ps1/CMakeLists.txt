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
elseif(DEFINED FUNKIN_PS1_AUDIO_VAG)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_VAG has been superseded; provide FUNKIN_PS1_AUDIO_WAV")
elseif(DEFINED FUNKIN_PS1_AUDIO_WAV)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_WAV does not name an existing PCM WAV file")
endif()
