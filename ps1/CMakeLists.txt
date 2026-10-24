cmake_minimum_required(VERSION 3.21)

project(funkin_ps1_probe LANGUAGES C CXX ASM VERSION 0.1.0)

psn00bsdk_add_executable(funkin-ps1-probe GPREL main.c)

psn00bsdk_add_cd_image(
	ps1-disc
	funkin-ps1-probe
	iso.xml
	DEPENDS funkin-ps1-probe system.cnf
)
