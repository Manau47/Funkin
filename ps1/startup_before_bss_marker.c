/*
 * Startup diagnostic that stops before clearing the linked executable BSS.
 * It uses the real playable target and keeps main linked, but never enters it.
 */

#include <stdint.h>
#define GPU_GP0 (*(volatile uint32_t *)0x1F801810u)
#define GPU_GP1 (*(volatile uint32_t *)0x1F801814u)

extern int main(void);

/* Keep the real game code linked; this initialized gate remains nonzero. */
static volatile uint32_t startup_release_code = 0xFFFFFFFFu;

void _start_inner(int argc, const char **argv)
{
	(void)argc;
	(void)argv;

	if (startup_release_code == 0u)
		(void)main();

	/*
	 * Configure a 320x240 NTSC display directly. Avoid PSn00bSDK GPU helpers
	 * here: ResetGraph/PutDispEnv use callback state and _gpu_video_mode in BSS,
	 * which the CRT has not initialized at this checkpoint.
	 */
	GPU_GP1 = 0x00000000u; /* GP1(00): reset GPU */
	GPU_GP1 = 0x01000000u; /* GP1(01): reset command buffer */
	GPU_GP1 = 0x02000000u; /* GP1(02): acknowledge GPU IRQ */
	GPU_GP1 = 0x03000001u; /* GP1(03): disable display during setup */
	GPU_GP1 = 0x04000000u; /* GP1(04): DMA off */
	GPU_GP1 = 0x05000000u; /* GP1(05): display start (0,0) */
	GPU_GP1 = 0x06C60260u; /* GP1(06): SDK 320x240 default horizontal range */
	GPU_GP1 = 0x07040010u; /* GP1(07): 240-line NTSC vertical range */
	GPU_GP1 = 0x08000001u; /* GP1(08): 320x240, NTSC, 15-bit */

	GPU_GP0 = 0xE3000000u; /* GP0(E3): drawing area top-left (0,0) */
	GPU_GP0 = 0xE403BD3Fu; /* GP0(E4): drawing area bottom-right (319,239) */
	GPU_GP0 = 0x0200FFFFu; /* GP0(02): cyan fill rectangle */
	GPU_GP0 = 0x00000000u; /* origin (0,0) */
	GPU_GP0 = 0x00F00140u; /* 320x240 */
	GPU_GP1 = 0x03000000u; /* GP1(03): enable display */

	for (;;)
		__asm__ volatile("nop");
}
