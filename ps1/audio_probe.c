/* CD-DA position probe. The WAV track is supplied locally at CMake time. */
#include <stdint.h>
#include <stdio.h>
#include <psxapi.h>
#include <psxgpu.h>
#include <psxcd.h>

#define SCREEN_W 320
#define SCREEN_H 240
#define OT_LENGTH 8
#define PACKET_BYTES 4096
#define TEST_BPM 120
#define AUDIO_TRACK 2

typedef struct {
	DISPENV display;
	DRAWENV draw;
	uint32_t ot[OT_LENGTH];
	uint8_t packets[PACKET_BYTES];
} Frame;

static Frame frames[2];
static int draw_index;
static uint8_t *packet_cursor;

static void init_video(void)
{
	ResetGraph(0);
	FntLoad(960, 0);
	for (int i = 0; i < 2; i++) {
		SetDefDrawEnv(&frames[i].draw, 0, i * SCREEN_H, SCREEN_W, SCREEN_H);
		SetDefDispEnv(&frames[i].display, 0, i * SCREEN_H, SCREEN_W, SCREEN_H);
		setRGB0(&frames[i].draw, 8, 8, 20);
		frames[i].draw.isbg = 1;
		ClearOTagR(frames[i].ot, OT_LENGTH);
	}
	draw_index = 0;
	packet_cursor = frames[0].packets;
	SetDispMask(1);
}

static void draw_text(int x, int y, const char *text)
{
	packet_cursor = (uint8_t *)FntSort(frames[draw_index].ot, packet_cursor, x, y, text);
}

static void display_frame(void)
{
	int display_index = draw_index ^ 1;
	ClearOTagR(frames[draw_index].ot, OT_LENGTH);
	packet_cursor = frames[draw_index].packets;
	DrawSync(0);
	VSync(0);
	PutDispEnv(&frames[display_index].display);
	DrawOTagEnv(&frames[draw_index].ot[OT_LENGTH - 1], &frames[draw_index].draw);
	draw_index = display_index;
}

static unsigned bcd_to_uint(uint8_t value)
{
	return (unsigned)((value >> 4) * 10 + (value & 0x0F));
}

static unsigned track_position_ms(const CdlLOCINFOP *position)
{
	unsigned minutes = bcd_to_uint(position->track_minute);
	unsigned seconds = bcd_to_uint(position->track_second);
	unsigned sectors = bcd_to_uint(position->track_sector);
	return ((minutes * 60u + seconds) * 75u + sectors) * 1000u / 75u;
}

int main(void)
{
	init_video();
	CdInit();
	CdControlB(CdlPause, 0, 0);
	uint8_t track = AUDIO_TRACK;
	CdControl(CdlPlay, &track, 0);

	for (;;) {
		CdlLOCINFOP position = {0};
		CdControlB(CdlGetlocP, 0, (uint8_t *)&position);
		unsigned milliseconds = track_position_ms(&position);
		unsigned beat_period_ms = 60000u / TEST_BPM;
		unsigned beat_phase_ms = milliseconds % beat_period_ms;
		char line[64];
		sprintf(line, "CD AUDIO %02u:%02u.%03u",
			milliseconds / 60000u, (milliseconds / 1000u) % 60u,
			milliseconds % 1000u);

		draw_text(16, 24, "PS1 CD-DA AUDIO POSITION");
		draw_text(16, 64, line);
		draw_text(16, 104, (beat_phase_ms < 90u) ? ">>> BEAT <<<" : "    beat    ");
		draw_text(16, 152, "120 BPM CLICK TRACK / 12 SECONDS");
		draw_text(16, 188, "POSITION FROM CD SUBCHANNEL Q");
		draw_text(16, 210, "SYNTHETIC TECHNICAL TEST ONLY");
		display_frame();
	}
	return 0;
}
