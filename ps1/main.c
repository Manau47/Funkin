/* Minimal PS1 video and controller probe for the unofficial FNF port. */
#include <stdint.h>
#include <stdio.h>
#include <psxapi.h>
#include <psxgpu.h>
#include <psxpad.h>

#define SCREEN_W 320
#define SCREEN_H 240
#define OT_LENGTH 8
#define PACKET_BYTES 8192
#define PAD_BYTES 34

typedef struct {
	DISPENV display;
	DRAWENV draw;
	uint32_t ot[OT_LENGTH];
	uint8_t packets[PACKET_BYTES];
} Frame;

typedef struct {
	uint16_t buttons;
	uint16_t previous_buttons;
	uint16_t pressed_edges;
	uint16_t released_edges;
	uint16_t held_frames;
	uint16_t last_hold_frames;
	uint8_t status;
	uint8_t type;
	uint8_t connected;
	uint8_t was_connected;
} PlayerInput;

static Frame frames[2];
static int draw_index;
static uint8_t *packet_cursor;
static char pad_buffers[2][PAD_BYTES];

static void init_video(void)
{
	ResetGraph(0);
	FntLoad(960, 0);

	for (int i = 0; i < 2; i++) {
		SetDefDrawEnv(&frames[i].draw, 0, i * SCREEN_H, SCREEN_W, SCREEN_H);
		SetDefDispEnv(&frames[i].display, 0, i * SCREEN_H, SCREEN_W, SCREEN_H);
		setRGB0(&frames[i].draw, 12, 12, 28);
		frames[i].draw.isbg = 1;
		ClearOTagR(frames[i].ot, OT_LENGTH);
	}

	draw_index = 0;
	packet_cursor = frames[draw_index].packets;
	SetDispMask(1);
}

static void begin_frame(void)
{
	ClearOTagR(frames[draw_index].ot, OT_LENGTH);
	packet_cursor = frames[draw_index].packets;
}

static void draw_text(int x, int y, const char *text)
{
	packet_cursor = (uint8_t *)FntSort(
		frames[draw_index].ot, packet_cursor, x, y, text);
}

static void end_frame(void)
{
	int display_index = draw_index ^ 1;
	DrawSync(0);
	VSync(0);
	PutDispEnv(&frames[display_index].display);
	DrawOTagEnv(&frames[draw_index].ot[OT_LENGTH - 1],
		&frames[draw_index].draw);
	draw_index = display_index;
}

static void poll_player_inputs(PlayerInput players[2])
{
	PADTYPE *pad = (PADTYPE *)&pad_buffers[0][0];
	players[0].status = pad->stat;
	players[0].type = pad->type;
	players[0].connected = (pad->stat == 0);
	if (players[0].connected) {
		players[0].buttons = (uint16_t)pad->btn;
		if (!players[0].was_connected) {
			players[0].previous_buttons = players[0].buttons;
			players[0].pressed_edges = 0;
			players[0].released_edges = 0;
			players[0].held_frames = 0;
		} else {
			players[0].pressed_edges = players[0].previous_buttons & ~players[0].buttons;
			players[0].released_edges = ~players[0].previous_buttons & players[0].buttons;
			if (players[0].buttons != 0xFFFF) {
				if (players[0].held_frames < 0xFFFF)
					players[0].held_frames++;
			} else {
				if (players[0].released_edges)
					players[0].last_hold_frames = players[0].held_frames;
				players[0].held_frames = 0;
			}
			players[0].previous_buttons = players[0].buttons;
		}
		players[0].was_connected = 1;
	} else {
		players[0].buttons = 0xFFFF;
		players[0].previous_buttons = 0xFFFF;
		players[0].pressed_edges = 0;
		players[0].released_edges = 0;
		players[0].held_frames = 0;
		players[0].was_connected = 0;
	}

	/* Keep player 2's input state separate for the planned local multiplayer. */
	players[1].status = 0xFF;
	players[1].type = 0;
	players[1].connected = 0;
	players[1].buttons = 0xFFFF;
}

static const char *button_state(const PlayerInput *player, uint16_t mask)
{
	return player->connected && !(player->buttons & mask) ? "ON " : "---";
}

int main(void)
{
	PlayerInput players[2] = {0};
	char status[64];
	char controls[256];
	char input_debug[96];
	char edge_debug[96];

	init_video();
	InitPAD(&pad_buffers[0][0], PAD_BYTES,
		&pad_buffers[1][0], PAD_BYTES);
	StartPAD();
	ChangeClearPAD(0);

	for (;;) {
		poll_player_inputs(players);
		begin_frame();

		draw_text(16, 20, "FUNKIN' / PLAYSTATION\nTECHNICAL INPUT TEST\n");
		if (players[0].connected)
		sprintf(status, "P1 CONNECTED   PAD TYPE: %02X\n", players[0].type);
		else
		sprintf(status, "P1 NOT CONNECTED  STATUS: %02X\n", players[0].status);
		draw_text(16, 64, status);

		sprintf(controls,
			"D-PAD  UP %s  DOWN %s\n"
			"       LEFT %s RIGHT %s\n"
			"FACE   TRIANGLE %s CIRCLE %s\n"
			"       CROSS %s SQUARE %s\n"
			"OTHER  START %s SELECT %s\n"
			"       L1 %s L2 %s R1 %s R2 %s\n",
			button_state(&players[0], PAD_UP),
			button_state(&players[0], PAD_DOWN),
			button_state(&players[0], PAD_LEFT),
			button_state(&players[0], PAD_RIGHT),
			button_state(&players[0], PAD_TRIANGLE),
			button_state(&players[0], PAD_CIRCLE),
			button_state(&players[0], PAD_CROSS),
			button_state(&players[0], PAD_SQUARE),
			button_state(&players[0], PAD_START),
			button_state(&players[0], PAD_SELECT),
			button_state(&players[0], PAD_L1),
			button_state(&players[0], PAD_L2),
			button_state(&players[0], PAD_R1),
			button_state(&players[0], PAD_R2));
		draw_text(16, 96, controls);
		unsigned active_buttons = 0;
		for (unsigned bit = 0; bit < 16; bit++)
			active_buttons += !(players[0].buttons & (1u << bit));
		sprintf(input_debug, "ACTIVE: %u   HOLD: %u FRAMES   LAST: %u",
			active_buttons, players[0].held_frames, players[0].last_hold_frames);
		sprintf(edge_debug, "PRESSED: %04X   RELEASED: %04X",
			(unsigned)players[0].pressed_edges, (unsigned)players[0].released_edges);
		draw_text(16, 176, input_debug);
		draw_text(16, 190, edge_debug);
		draw_text(16, 218, "P1/P2 INPUT STATES ARE SEPARATE");

		end_frame();
	}

	return 0;
}

