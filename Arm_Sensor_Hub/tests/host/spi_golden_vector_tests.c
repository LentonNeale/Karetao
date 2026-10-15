/**
 * @file spi_golden_vector_tests.c
 * @brief Asserts the shared SPI golden frames (shared/test-vectors/spi/frames.txt) against the
 *        protocol module, byte for byte.
 *
 * Each vector is one transaction: the STM32 state before it, the request the Pi sent, the
 * result the firmware reports and the response it stages. The test puts spi_protocol.c in that
 * state, feeds it the request and compares all SPI_FRAME_MAX_BYTES response bytes with the
 * vector. The Python suite (RaspberryPi_Sensor_Hub/tests/spi/test_golden_vectors.py) asserts
 * the same file from the Pi side, which is how the acceptance clause of SYS-SPI-001 ("the C and
 * Python protocol tests exchange the same frames bit-for-bit") is met.
 *
 * The file format is plain text (README.md next to the file): `[name]` opens a vector,
 * `key = value` lines fill it, `#` starts a comment, hex values are wire-order byte strings.
 * Checks report the vector and the failing comparison instead of a bare assert, so a mismatch
 * names the byte that differs.
 */

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "host_test_assert.h"

#include "crc32_iso_hdlc.h"
#include "spi_payload_layout.h"
#include "spi_protocol.h"

#define GOLDEN_MAX_LINE 4096u
#define GOLDEN_MAX_NAME 64u
#define GOLDEN_MAX_EXPECT 32u

typedef struct {
    bool present;
    bool has_type;
    bool has_seq;
    bool has_frame_time_us;
    bool has_payload;
    uint8_t type;
    uint32_t seq;
    uint64_t frame_time_us;
    uint8_t payload[SPI_PAYLOAD_MAX_BYTES];
    uint16_t payload_length;
} GoldenFrameFields;

typedef struct {
    char name[GOLDEN_MAX_NAME];
    bool has_next_tx_seq;
    uint32_t next_tx_seq;
    bool has_last_request_seq_key;
    bool has_last_request_seq;
    uint32_t last_request_seq;
    bool has_now_us;
    uint64_t now_us;
    bool has_staged;
    uint8_t staged[SPI_PAYLOAD_MAX_BYTES];
    uint16_t staged_length;
    bool has_request;
    uint8_t request[SPI_FRAME_MAX_BYTES];
    uint16_t request_length;
    GoldenFrameFields request_fields;
    char expect[GOLDEN_MAX_EXPECT];
    bool has_response;
    uint8_t response[SPI_FRAME_MAX_BYTES];
    uint16_t response_length;
    GoldenFrameFields response_fields;
} GoldenVector;

static uint64_t s_now_us;

/* spi_protocol.c stamps frame_time_us from the time service; the vector sets the clock. */
uint64_t TimeService_NowUs(void)
{
    return s_now_us;
}

static void Fail(const GoldenVector *vector, const char *what)
{
    fprintf(stderr, "spi_golden_vector_tests: [%s] %s\n", (vector != NULL) ? vector->name : "(file)", what);
    exit(EXIT_FAILURE);
}

static void FailAt(const GoldenVector *vector, const char *which, size_t offset, unsigned actual, unsigned expected)
{
    fprintf(stderr, "spi_golden_vector_tests: [%s] %s byte %zu is 0x%02X, vector says 0x%02X\n",
            vector->name, which, offset, actual, expected);
    exit(EXIT_FAILURE);
}

static const struct {
    const char *name;
    SpiProtocol_Result result;
} s_results[] = {
    {"OK", SPI_PROTOCOL_OK},
    {"BAD_MAGIC", SPI_PROTOCOL_BAD_MAGIC},
    {"BAD_VERSION", SPI_PROTOCOL_BAD_VERSION},
    {"BAD_LENGTH", SPI_PROTOCOL_BAD_LENGTH},
    {"BAD_CRC", SPI_PROTOCOL_BAD_CRC},
    {"BAD_SEQUENCE", SPI_PROTOCOL_BAD_SEQUENCE},
    {"BAD_MESSAGE", SPI_PROTOCOL_BAD_MESSAGE},
    {"BAD_TIME_SYNC", SPI_PROTOCOL_BAD_TIME_SYNC},
    {"BAD_STATE", SPI_PROTOCOL_BAD_STATE},
};

static bool LookupResult(const char *name, SpiProtocol_Result *result)
{
    size_t index;
    for (index = 0u; index < sizeof(s_results) / sizeof(s_results[0]); ++index) {
        if (strcmp(name, s_results[index].name) == 0) {
            *result = s_results[index].result;
            return true;
        }
    }
    return false;
}

static const char *ResultName(SpiProtocol_Result result)
{
    size_t index;
    for (index = 0u; index < sizeof(s_results) / sizeof(s_results[0]); ++index) {
        if (s_results[index].result == result) {
            return s_results[index].name;
        }
    }
    return "(unknown)";
}

static bool IsSpace(char c)
{
    return (c == ' ') || (c == '\t') || (c == '\r') || (c == '\n');
}

static char *Trim(char *text)
{
    char *end;
    while (IsSpace(*text)) {
        ++text;
    }
    end = text + strlen(text);
    while ((end > text) && IsSpace(end[-1])) {
        --end;
    }
    *end = '\0';
    return text;
}

static int HexDigit(char c)
{
    if ((c >= '0') && (c <= '9')) return c - '0';
    if ((c >= 'a') && (c <= 'f')) return 10 + (c - 'a');
    if ((c >= 'A') && (c <= 'F')) return 10 + (c - 'A');
    return -1;
}

static bool ParseHex(const char *text, uint8_t *out, size_t capacity, uint16_t *length)
{
    size_t count = 0u;
    while (*text != '\0') {
        int high;
        int low;
        if (IsSpace(*text)) {
            ++text;
            continue;
        }
        high = HexDigit(text[0]);
        low = (text[1] != '\0') ? HexDigit(text[1]) : -1;
        if ((high < 0) || (low < 0) || (count >= capacity)) {
            return false;
        }
        out[count++] = (uint8_t)((high << 4) | low);
        text += 2;
    }
    *length = (uint16_t)count;
    return true;
}

static bool ParseU64(const char *text, uint64_t *value)
{
    char *end = NULL;
    if (*text == '\0') {
        return false;
    }
    *value = strtoull(text, &end, 0);
    return (end != NULL) && (*end == '\0');
}

static bool ParseU32(const char *text, uint32_t *value)
{
    uint64_t wide;
    if (!ParseU64(text, &wide) || (wide > UINT32_MAX)) {
        return false;
    }
    *value = (uint32_t)wide;
    return true;
}

static void SetFrameField(GoldenVector *vector, GoldenFrameFields *fields, const char *key, const char *value)
{
    uint64_t number;
    fields->present = true;
    if (strcmp(key, "type") == 0) {
        if (!ParseU64(value, &number) || (number > UINT8_MAX)) Fail(vector, "bad .type");
        fields->type = (uint8_t)number;
        fields->has_type = true;
    } else if (strcmp(key, "seq") == 0) {
        if (!ParseU32(value, &fields->seq)) Fail(vector, "bad .seq");
        fields->has_seq = true;
    } else if (strcmp(key, "frame_time_us") == 0) {
        if (!ParseU64(value, &fields->frame_time_us)) Fail(vector, "bad .frame_time_us");
        fields->has_frame_time_us = true;
    } else if (strcmp(key, "payload") == 0) {
        if (!ParseHex(value, fields->payload, sizeof(fields->payload), &fields->payload_length)) Fail(vector, "bad .payload hex");
        fields->has_payload = true;
    } else {
        Fail(vector, "unknown frame field");
    }
}

static void SetKey(GoldenVector *vector, const char *key, const char *value)
{
    if (strcmp(key, "description") == 0) {
        return;
    }
    if (strcmp(key, "stm32.next_tx_seq") == 0) {
        if (!ParseU32(value, &vector->next_tx_seq)) Fail(vector, "bad stm32.next_tx_seq");
        vector->has_next_tx_seq = true;
    } else if (strcmp(key, "stm32.last_request_seq") == 0) {
        vector->has_last_request_seq_key = true;
        if (strcmp(value, "none") == 0) {
            vector->has_last_request_seq = false;
        } else {
            if (!ParseU32(value, &vector->last_request_seq)) Fail(vector, "bad stm32.last_request_seq");
            vector->has_last_request_seq = true;
        }
    } else if (strcmp(key, "stm32.now_us") == 0) {
        if (!ParseU64(value, &vector->now_us)) Fail(vector, "bad stm32.now_us");
        vector->has_now_us = true;
    } else if (strcmp(key, "stm32.staged_snapshot") == 0) {
        if (!ParseHex(value, vector->staged, sizeof(vector->staged), &vector->staged_length)) Fail(vector, "bad stm32.staged_snapshot hex");
        vector->has_staged = true;
    } else if (strcmp(key, "request") == 0) {
        if (!ParseHex(value, vector->request, sizeof(vector->request), &vector->request_length)) Fail(vector, "bad request hex");
        vector->has_request = true;
    } else if (strncmp(key, "request.", 8u) == 0) {
        SetFrameField(vector, &vector->request_fields, key + 8, value);
    } else if (strcmp(key, "expect") == 0) {
        if (strlen(value) >= sizeof(vector->expect)) Fail(vector, "expect too long");
        strcpy(vector->expect, value);
    } else if (strcmp(key, "response") == 0) {
        if (!ParseHex(value, vector->response, sizeof(vector->response), &vector->response_length)) Fail(vector, "bad response hex");
        vector->has_response = true;
    } else if (strncmp(key, "response.", 9u) == 0) {
        SetFrameField(vector, &vector->response_fields, key + 9, value);
    } else {
        fprintf(stderr, "spi_golden_vector_tests: [%s] unknown key '%s'\n", vector->name, key);
        exit(EXIT_FAILURE);
    }
}

static uint16_t ReadU16(const uint8_t *data)
{
    return (uint16_t)data[0] | ((uint16_t)data[1] << 8u);
}

static uint32_t ReadU32(const uint8_t *data)
{
    return (uint32_t)data[0] | ((uint32_t)data[1] << 8u) | ((uint32_t)data[2] << 16u) | ((uint32_t)data[3] << 24u);
}

static uint64_t ReadU64(const uint8_t *data)
{
    return (uint64_t)ReadU32(data) | ((uint64_t)ReadU32(data + 4) << 32u);
}

/* The header read through the layout macros must say what the vector's decoded fields say,
 * and the CRC must cover exactly header plus payload. This is the C side decoding a frame. */
static void CheckFrameFields(const GoldenVector *vector, const uint8_t frame[SPI_FRAME_MAX_BYTES],
                             uint16_t frame_length, const GoldenFrameFields *fields, const char *which)
{
    uint16_t payload_length = ReadU16(&frame[SPI_FRAME_OFFSET_PAYLOAD_LENGTH]);
    char message[96];

    if (ReadU16(&frame[SPI_FRAME_OFFSET_MAGIC]) != SPI_FRAME_MAGIC) {
        snprintf(message, sizeof(message), "%s magic is not SPI_FRAME_MAGIC", which); Fail(vector, message);
    }
    if (frame[SPI_FRAME_OFFSET_PROTOCOL_VERSION] != SPI_PROTOCOL_VERSION) {
        snprintf(message, sizeof(message), "%s protocol_version is not SPI_PROTOCOL_VERSION", which); Fail(vector, message);
    }
    if (frame[SPI_FRAME_OFFSET_MESSAGE_TYPE] != fields->type) {
        snprintf(message, sizeof(message), "%s message_type differs from .type", which); Fail(vector, message);
    }
    if (payload_length != fields->payload_length) {
        snprintf(message, sizeof(message), "%s payload_len differs from the .payload length", which); Fail(vector, message);
    }
    if (ReadU32(&frame[SPI_FRAME_OFFSET_SEQUENCE]) != fields->seq) {
        snprintf(message, sizeof(message), "%s seq differs from .seq", which); Fail(vector, message);
    }
    if (ReadU64(&frame[SPI_FRAME_OFFSET_TIME_US]) != fields->frame_time_us) {
        snprintf(message, sizeof(message), "%s frame_time_us differs from .frame_time_us", which); Fail(vector, message);
    }
    if (memcmp(&frame[SPI_FRAME_OFFSET_PAYLOAD], fields->payload, payload_length) != 0) {
        snprintf(message, sizeof(message), "%s payload bytes differ from .payload", which); Fail(vector, message);
    }
    if (frame_length != (uint16_t)(SPI_FRAME_CRC_OFFSET(payload_length) + SPI_FRAME_CRC_BYTES)) {
        snprintf(message, sizeof(message), "%s hex length is not header + payload + CRC", which); Fail(vector, message);
    }
    if (!Crc32IsoHdlc_Verify(frame, SPI_FRAME_HEADER_BYTES + payload_length, &frame[SPI_FRAME_CRC_OFFSET(payload_length)])) {
        snprintf(message, sizeof(message), "%s CRC does not verify", which); Fail(vector, message);
    }
}

/* The same rules the Python loader enforces: all four fields or none, a response with fields. */
static void CheckVectorShape(const GoldenVector *vector)
{
    const GoldenFrameFields *sets[2] = {&vector->request_fields, &vector->response_fields};
    size_t index;
    for (index = 0u; index < 2u; ++index) {
        const GoldenFrameFields *fields = sets[index];
        if (fields->present && !(fields->has_type && fields->has_seq && fields->has_frame_time_us && fields->has_payload)) {
            Fail(vector, (index == 0u) ? "request fields incomplete (type, seq, frame_time_us, payload)"
                                       : "response fields incomplete (type, seq, frame_time_us, payload)");
        }
    }
    if (vector->has_response && !vector->response_fields.present) {
        Fail(vector, "a response needs its response.* fields");
    }
    if (vector->request_fields.present && !vector->has_request) {
        Fail(vector, "request.* fields without a request");
    }
}

static void RunVector(const GoldenVector *vector)
{
    SpiProtocol_State state;
    SpiProtocol_Result expected;
    SpiProtocol_Result result;
    uint8_t request[SPI_FRAME_MAX_BYTES];
    uint8_t response[SPI_FRAME_MAX_BYTES];
    uint8_t expected_response[SPI_FRAME_MAX_BYTES];
    size_t offset;

    if (!vector->has_next_tx_seq || !vector->has_now_us || !vector->has_last_request_seq_key) {
        Fail(vector, "stm32.next_tx_seq, stm32.last_request_seq and stm32.now_us are required");
    }
    if (!LookupResult(vector->expect, &expected)) {
        Fail(vector, "expect is not a SpiProtocol_Result name");
    }
    CheckVectorShape(vector);

    SpiProtocol_Init(&state);
    state.next_tx_sequence = vector->next_tx_seq;
    state.has_request_sequence = vector->has_last_request_seq;
    state.last_request_sequence = vector->last_request_seq;
    s_now_us = vector->now_us;
    if (vector->has_staged && !SpiProtocol_SetUnsolicitedSnapshot(&state, vector->staged, vector->staged_length)) {
        Fail(vector, "SpiProtocol_SetUnsolicitedSnapshot rejected stm32.staged_snapshot");
    }

    memset(response, 0xAA, sizeof(response));
    if (!vector->has_request) {
        if (expected != SPI_PROTOCOL_OK) Fail(vector, "a vector without a request can only expect OK");
        if (SpiProtocol_BuildBootStatus(&state, response) != SPI_PROTOCOL_OK) Fail(vector, "SpiProtocol_BuildBootStatus failed");
    } else {
        memset(request, 0, sizeof(request));
        memcpy(request, vector->request, vector->request_length);
        if (vector->request_fields.present) {
            CheckFrameFields(vector, request, vector->request_length, &vector->request_fields, "request");
        }
        result = SpiProtocol_ProcessRequest(&state, request, response);
        if (result != expected) {
            fprintf(stderr, "spi_golden_vector_tests: [%s] firmware reported %s, vector expects %s\n",
                    vector->name, ResultName(result), vector->expect);
            exit(EXIT_FAILURE);
        }
    }

    /* The state after the transaction follows from the result (SPI_SYSTEM_INTERFACE.md section 14:
     * a rejected frame modifies no application state; section 4: an accepted request becomes the
     * sequence high-water mark; a sent SNAPSHOT is no longer pending). */
    if (vector->has_request && (expected != SPI_PROTOCOL_OK)) {
        if ((state.has_request_sequence != vector->has_last_request_seq) ||
            (state.has_request_sequence && (state.last_request_sequence != vector->last_request_seq))) {
            Fail(vector, "a rejected request changed the accepted-sequence state");
        }
        if (state.unsolicited_pending != vector->has_staged) {
            Fail(vector, "a rejected request changed the staged snapshot");
        }
    }
    if (vector->has_request && (expected == SPI_PROTOCOL_OK)) {
        if (!state.has_request_sequence || (state.last_request_sequence != ReadU32(&request[SPI_FRAME_OFFSET_SEQUENCE]))) {
            Fail(vector, "an accepted request did not become the sequence high-water mark");
        }
    }
    if (vector->has_response && vector->response_fields.present) {
        if (state.unsolicited_pending == (vector->response_fields.type == SPI_MESSAGE_SNAPSHOT) && vector->has_staged) {
            Fail(vector, "a staged snapshot must stop pending exactly when it is sent");
        }
    }
    if (state.next_tx_sequence != vector->next_tx_seq + 1u) {
        Fail(vector, "exactly one response must consume one transmit sequence number");
    }

    if (vector->has_response) {
        memset(expected_response, 0, sizeof(expected_response));
        memcpy(expected_response, vector->response, vector->response_length);
        for (offset = 0u; offset < SPI_FRAME_MAX_BYTES; ++offset) {
            if (response[offset] != expected_response[offset]) {
                FailAt(vector, "response", offset, response[offset], expected_response[offset]);
            }
        }
        if (vector->response_fields.present) {
            CheckFrameFields(vector, response, vector->response_length, &vector->response_fields, "response");
        }
    }
}

int main(int argc, char **argv)
{
    static char line[GOLDEN_MAX_LINE];
    static GoldenVector vector;
    FILE *file;
    bool in_vector = false;
    unsigned count = 0u;
    unsigned line_number = 0u;

    if (argc != 2) {
        fprintf(stderr, "usage: spi_golden_vector_tests <path to frames.txt>\n");
        return EXIT_FAILURE;
    }
    file = fopen(argv[1], "r");
    if (file == NULL) {
        fprintf(stderr, "spi_golden_vector_tests: cannot open %s\n", argv[1]);
        return EXIT_FAILURE;
    }

    while (fgets(line, (int)sizeof(line), file) != NULL) {
        char *text;
        char *equals;
        ++line_number;
        if ((strchr(line, '\n') == NULL) && !feof(file)) {
            fprintf(stderr, "spi_golden_vector_tests: line %u exceeds %u characters\n", line_number, GOLDEN_MAX_LINE);
            return EXIT_FAILURE;
        }
        text = Trim(line);
        if ((*text == '\0') || (*text == '#')) {
            continue;
        }
        if (*text == '[') {
            char *close = strchr(text, ']');
            if (in_vector) {
                RunVector(&vector);
                ++count;
            }
            memset(&vector, 0, sizeof(vector));
            if ((close == NULL) || (close[1] != '\0') || ((size_t)(close - text) >= sizeof(vector.name))) {
                fprintf(stderr, "spi_golden_vector_tests: line %u: bad vector header\n", line_number);
                return EXIT_FAILURE;
            }
            *close = '\0';
            strcpy(vector.name, text + 1);
            in_vector = true;
            continue;
        }
        equals = strchr(text, '=');
        if (!in_vector || (equals == NULL)) {
            fprintf(stderr, "spi_golden_vector_tests: line %u: expected 'key = value' inside a vector\n", line_number);
            return EXIT_FAILURE;
        }
        *equals = '\0';
        SetKey(&vector, Trim(text), Trim(equals + 1));
    }
    if (in_vector) {
        RunVector(&vector);
        ++count;
    }
    fclose(file);

    if (count == 0u) {
        fprintf(stderr, "spi_golden_vector_tests: %s holds no vectors\n", argv[1]);
        return EXIT_FAILURE;
    }
    printf("spi_golden_vector_tests: %u vectors asserted from %s\n", count, argv[1]);
    return EXIT_SUCCESS;
}
