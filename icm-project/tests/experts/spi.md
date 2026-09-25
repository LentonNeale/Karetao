# SPI subject-expert checks
<!-- Each "## " heading is one question. expect: any of the |-separated strings must appear in the answer
     (case-insensitive). basis: any of the |-separated labels must appear on the Basis line. -->

## What is the maximum payload size of an SPI frame, and the fixed frame size?
expect: 490
basis: documented

## Which STM32 pin is DATA_READY, and is its assignment settled?
expect: PA8
basis: conflict

## Does the firmware implement the GET_DIAGNOSTIC request?
expect: not implemented|no,|does not|isn't|is not
basis: not documented|documented|implemented|open

## What does the STM32 currently send back for a GET_STATUS request?
expect: ACK
basis: implemented

## Which SPI mode does the link use?
expect: mode 0|CPOL=0|CPOL = 0
basis: documented

## What bit rate does the CAN bus run at?
expect: not documented|outside|out of scope|not part of|not cover
basis: not documented
