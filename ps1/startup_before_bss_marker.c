/*
 * Startup diagnostic that stops before clearing the linked executable BSS.
 * It uses the real playable target and keeps main linked, but never enters it.
 */

#include <stdint.h>
#include <psxapi.h>

#define STARTUP_MARKER_W 320
#define STARTUP_MARKER_H 240

extern int main(void);

/* Keep the real game code linked; this initialized gate remains nonzero. */
static volatile uint32_t startup_release_code = 0xFFFFFFFFu;

void _start_inner(int argc, const char **argv)
{
	(void)argc;
	(void)argv;

	volatile uint32_t *gp0 = (volatile uint32_t *)0x1F801810;
	if (startup_release_code == 0u)
		(void)main();
	for (;;)
	{
		/* GP0 fill-rectangle command: cyan, at (0,0), 320x240. */
		gp0[0] = 0x0200FFFFu;
		gp0[0] = 0u;
		gp0[0] = (STARTUP_MARKER_H << 16) | STARTUP_MARKER_W;
		VSync(0);
	}
}
