# Raspberry Pi 5 Bring-Up Guide

## Ubuntu Server 24.04 LTS, cloud-init, PREEMPT_RT, ROS 2 Jazzy and STM32 SPI host

**Component:** Raspberry Sensor Hub (Karetao host-side integration component)
**Document class:** Component implementation / provisioning procedure
**Revision:** 0.1, rewritten 2026-09-20 (see Appendix A for the conflict review that drove the rewrite)

M

---

## Authority and references

This document is Raspberry Sensor Hub implementation authority. It describes **how** the Raspberry Pi host is provisioned and qualified. It does **not** define system requirements, and where it quotes a system value it cites the Karetao identifier that owns it. If this document and a Karetao system document disagree, the Karetao document wins and this document must be corrected.

Karetao system documents this procedure depends on:

| Subject | Authoritative document |
| --- | --- |
| System requirements (SYS-* identifiers) | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` |
| SPI transport, framing, DATA_READY, host responsibilities | `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` |
| SPI payloads | `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md` |
| Time authority and TIME_SYNC | `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` |
| Host heartbeat, command and state contract | `Documentation/02_INTERFACES/HOST/HOST_SYSTEM_INTERFACE.md` |
| Lifecycle states, restart and recovery rules | `Documentation/01_SYSTEM/SYSTEM_LIFECYCLE.md` |
| Safety release gates SAFE-001 to SAFE-009 | `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md`, `SAFETY_INTEGRATION.md` |
| Release conditions 1 to 7 | `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` Part 4 |
| System verification status | `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`, `INTEGRATION_GATES.md` |
| STM32 pin baseline (SPI3, DATA_READY PA8) | `Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md` |
| Host component role | `Documentation/03_COMPONENTS/RASPBERRY_SENSOR_HUB.md` |

The legacy names `SPI_CONTRACT.md`, `LIFECYCLE_CONTRACT.md` and `SAFETY_RELEASE_CHECKLIST.md` are no longer current. The checklist survives only as a non-normative archive copy under `Documentation/99_ARCHIVE/DECISIONS/`.

**Repository structure:** This document is part of the Karetao repository. The **RaspberryPi_Sensor_Hub** directory contains the component implementation (software source, tests, provisioning), and it references (but does not duplicate) the system contracts in **Documentation/**. When following this guide, clone the entire Karetao repository (Part D.1) so you have access to both the component code and the system authority documents.

System values used in this guide, with their owners:

| Value | Owner | Status per owner |
| --- | --- | --- |
| SPI Mode 0, 512-byte frame, 490-byte max payload, little-endian, CRC-32/ISO-HDLC | SYS-SPI-001 (SD-15) | Approved |
| SPI clock initial maximum 5 MHz | SYS-TIM-003 (SD-01, SD-15) | Provisional integration ceiling, not hardware approval |
| DATA_READY optional, 1 ms polling fallback, Pi is SPI clock master | SYS-SPI-003 (SD-17) | Approved; **physical Pi GPIO assignment is a harness decision, not a system-level one.** GPIO25 assigned and wired in E1, pending electrical validation |
| SPI cable length 20 to 30 cm | SYS-SPI-004 | Proposed; measurement required |
| Pi is system time authority; TIME_SYNC 1 Hz nominal, up to 10 Hz; invalid after 5 s | SYS-SYNC-001/002 (SD-18, SD-19) | Approved |
| Pi heartbeat timeout 500 ms rejects motion | SYS-FAIL-001 (SD-03) | Approved |
| Restart returns to INACTIVE, explicit reactivation, never auto-resume motion | SYS-REC-002 (SD-24) | Approved |
| Baseline control-loop rate 100 Hz | SYS-TIM-001 (SD-01) | Baseline |
| Independent E-stop and motor-disable paths are release gates | SYS-SAFE-001 (SD-25), SAFE-001 to SAFE-009 | Open / blocked |

---

## Roles

The Raspberry Pi hosts the **Raspberry Sensor Hub**. It provides:

* SPI master and system time authority (SPI_SYSTEM_INTERFACE §1, §10)
* Periodic TIME_SYNC issue (SPI_SYSTEM_INTERFACE §13)
* Heartbeat toward the STM32 (HOST_SYSTEM_INTERFACE)
* Measurement and estimator history, EKF, ROS 2 execution (SD-09)
* Host-side diagnostics and component verification evidence

The STM32 **Arm Sensor Hub** remains responsible for sensor acquisition, CAN transport, lifecycle gating and command validation.

Neither the Pi, the STM32, nor the SPI link is an emergency stop. Independent E-stop and motor-disable paths are separate release gates (SAFE-002, SAFE-003). Application controls on either processor are supplementary controls only (SD-25). No component in this guide is "the final safety authority"; the system motion-permission authority is an open Karetao decision (SD-02, register issue #5).

**Do not energize motors on the strength of this procedure.** Energized motion requires release conditions 1 to 7 and SAFE-001 to SAFE-009, all currently open.

---

# Part A — Provisioning

## A1. Provisioning strategy

Two stages, deliberately separated:

1. **Imaging.** Raspberry Pi Imager writes the unmodified official Ubuntu Server 24.04 LTS arm64 image. No Imager customisation is used.
2. **First-boot configuration.** The `system-boot` partition is mounted on the workstation and its cloud-init NoCloud seed (`meta-data`, `network-config`, `user-data`) is replaced with the version-controlled Karetao seed from section A6.

```text
Raspberry Pi Imager ──► Ubuntu Server 24.04 LTS arm64 on SD/SSD
                              │
                              ▼
        Mount system-boot, replace cloud-init seed (A6)
                              │
                              ▼
        First boot ──► cloud-init provisions the machine
                              │
                    (optionally: clone Karetao repo from GitHub or offline source)
                              │
                              ▼
        Part D ──► Create ROS 2 workspace, link packages, build
                              │
                              ▼
        Manual qualification (Parts B to F) ──► component evidence
```

cloud-init owns everything that is repeatable machine configuration: OS packages, ROS, networking, systemd units, SSH keys. It does **not** own the application software (Karetao repository) — that is cloned separately in Part D and built into the workspace. The remainder of this guide qualifies the machine; it does not configure it by hand except where noted.

## A2. Hardware

* Raspberry Pi 5, 8 GB, official 27 W USB-C supply, active cooler.
* 32 GB or larger high-endurance microSD for commissioning; SSD for a deployed robot.
* Wired Ethernet on a DHCP network. Use Ethernet, not Wi-Fi, for commissioning.
* SPI harness to the STM32 SPI3 slave: 3.3 V signalling only, common ground, **20 to 30 cm cable (SYS-SPI-004)**. Record the cable length used.
* Separate emergency-stop and power-interlock path (SAFE-002, SAFE-003). Not part of this guide.
* Optional: USB-serial adapter on the Pi 5 UART debug connector, useful for watching boot and cloud-init console output. It cannot itself recover a locked-out account, since the image has no password login; the documented recovery route is the offline card repair in Appendix B.

Update the Pi bootloader EEPROM before first boot if required and do not interrupt power while doing so.

## A3. Install Raspberry Pi Imager

```bash
sudo snap install rpi-imager
rpi-imager
```

## A4. Write the image

In Raspberry Pi Imager select **Raspberry Pi 5 → Ubuntu → Ubuntu Server 24.04 LTS (64-bit)** and the target storage device. Verify the target device carefully; writing erases it.

When Imager offers OS customisation: **decline everything.** Do not set hostname, user, password, SSH keys, Wi-Fi, locale, timezone or keyboard. cloud-init owns all of these.

Let Imager finish writing and verifying. Do not boot the Pi yet.

## A5. Mount the boot partition

Eject and reinsert the card, then identify it:

```bash
lsblk -o NAME,SIZE,LABEL,MOUNTPOINTS
```

The first partition is labelled `system-boot` (FAT). Mount it if the desktop has not already:

```bash
udisksctl mount -b /dev/sdX1     # replace sdX1; do not guess
ls -la /media/$USER/system-boot/
```

You should see `meta-data`, `network-config`, `user-data` and `config.txt`. Record the image's original seed files before replacing them (copy them into the provisioning directory under `reference/` for the image version used).

## A6. Karetao cloud-init seed

The three files below are the machine provisioning source of truth. They are version-controlled at `RaspberryPi_Sensor_Hub/provisioning/cloud-init/` (see Part G). Copy them onto `system-boot`, replacing the image's originals.

### A6.0 Generate and select the SSH key

This step is what makes login passwordless: `ssh_pwauth: false` and `lock_passwd: true` in `user-data` (A6.4) mean the **only** way into the Pi is the public key placed in `ssh_authorized_keys`. Get this right before writing the card, since a wrong or placeholder key locks the Pi out until it is repaired offline (Appendix B).

Check whether a suitable key already exists on the workstation:

```bash
ls -l ~/.ssh/*.pub
```

If none exists, or a dedicated key is preferred for this robot, generate one:

```bash
ssh-keygen -t ed25519 -C "armpi" -f ~/.ssh/id_ed25519
```

Leave a passphrase set for a workstation key, or none for an unattended CI/build host; either is fine, since the passphrase protects only the local private key and never touches the Pi.

Print the exact public key line that must go into `user-data`:

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy that entire line, including the `ssh-ed25519` prefix and the trailing comment. Do not retype it and do not truncate it; a single dropped character produces a key that looks plausible but never authenticates.

### A6.1 Substitute before copying

| Placeholder | Replace with |
| --- | --- |
| `karetao-pi-01` | Unique DNS-safe hostname for this Pi |
| `ssh-ed25519 AAAA...REPLACE_WITH_PUBLIC_KEY...` | The **exact** line from `cat ~/.ssh/id_ed25519.pub` above, in full |
| `PROVISIONING_GIT_REV` | Git revision of the provisioning directory being deployed |

Never place a private key, an Ubuntu Pro token or any other secret in these files, on the card, or in the repository. The public key is not a secret and is safe to commit to `provisioning/cloud-init/user-data`.

**Before ejecting the card (fold into A8):** confirm the placeholder was actually replaced, and that what is on the card matches your local key, not just that it looks like a key:

```bash
grep 'ssh-ed25519' /media/$USER/system-boot/user-data
diff <(grep -o 'ssh-ed25519 .*' /media/$USER/system-boot/user-data) <(cat ~/.ssh/id_ed25519.pub)
```

The `diff` producing no output is the only pass condition. If it prints anything, or the `grep` still shows `REPLACE_WITH_PUBLIC_KEY`, fix `user-data` before continuing; do not boot the Pi on an unverified key.

### A6.2 `meta-data`

```yaml
instance-id: karetao-pi-01
local-hostname: karetao-pi-01
```

Change `instance-id` whenever `user-data` changes materially; cloud-init only re-runs first-boot modules for a new instance id.

### A6.3 `network-config`

Ubuntu's Raspberry Pi image pins the wired interface name to `eth0` through its own `10-raspi-eth0.link` rule, so `eth0` is stable here. DHCP is used during commissioning; do not introduce static addressing unless the deployment architecture requires it.

```yaml
version: 2
ethernets:
  eth0:
    dhcp4: true
    optional: true
```

### A6.4 `user-data`

```yaml
#cloud-config
# Karetao Raspberry Sensor Hub - Raspberry Pi 5 host provisioning
# Source of truth: RaspberryPi_Sensor_Hub/provisioning/cloud-init/user-data
# Target image: Ubuntu Server 24.04 LTS arm64 (Raspberry Pi preinstalled)
#
# Scope: repeatable base-machine provisioning only.
# Out of scope by design: Ubuntu Pro token, PREEMPT_RT enablement,
# SPI/GPIO hardware acceptance, robot workspace build, secrets.

hostname: karetao-pi-01
manage_etc_hosts: true
timezone: Pacific/Auckland
locale: en_NZ.UTF-8

# The image's default "ubuntu" user is intentionally NOT created
# (no "- default" entry below). The only account is "robot".
groups:
  - realtime

users:
  - name: robot
    gecos: Karetao Raspberry Sensor Hub
    shell: /bin/bash
    lock_passwd: true
    # dialout: Ubuntu's 60-gpio.rules grants spidev*, gpiochip* (pinctrl-rp1)
    #          and i2c-dev to this group. No custom udev rule is needed.
    # realtime: matched by /etc/security/limits.d/99-karetao-realtime.conf
    groups: [adm, dialout, plugdev, realtime]
    sudo: "ALL=(ALL) NOPASSWD:ALL"
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...REPLACE_WITH_PUBLIC_KEY...

disable_root: true
ssh_pwauth: false

package_update: true
package_upgrade: true
package_reboot_if_required: false   # a single controlled reboot is issued by power_state below

packages:
  # build and tooling
  - build-essential
  - cmake
  - ninja-build
  - git
  - pkg-config
  - curl
  - ca-certificates
  - gnupg
  - lsb-release
  - software-properties-common
  # time authority (replaces systemd-timesyncd)
  - chrony
  # host-side Python SPI/GPIO stack used by RaspberryPi_Sensor_Hub/src/spi
  - python3
  - python3-pip
  - python3-venv
  - python3-spidev
  - python3-libgpiod
  - gpiod
  - spi-tools
  - i2c-tools
  # real-time and load measurement
  - rt-tests
  - stress-ng
  # diagnostics
  - ethtool
  - htop
  - lm-sensors

write_files:

  # SSH hardening: key-only, single permitted account.
  - path: /etc/ssh/sshd_config.d/10-karetao.conf
    owner: root:root
    permissions: '0644'
    content: |
      PermitRootLogin no
      PasswordAuthentication no
      KbdInteractiveAuthentication no
      PubkeyAuthentication yes
      AllowUsers robot

  # Real-time scheduling limits for the "realtime" group only.
  # Values are commissioning defaults; RT priority actually used by the
  # controller is a controlled change (Part F).
  - path: /etc/security/limits.d/99-karetao-realtime.conf
    owner: root:root
    permissions: '0644'
    content: |
      @realtime soft rtprio 99
      @realtime hard rtprio 99
      @realtime soft priority 99
      @realtime hard priority 99
      @realtime soft memlock unlimited
      @realtime hard memlock unlimited

  # CPU governor: performance. Provisional; keep until a latency baseline
  # exists (Part B3). Implemented via sysfs so it does not depend on
  # kernel-specific linux-tools packages.
  - path: /etc/systemd/system/karetao-cpu-governor.service
    owner: root:root
    permissions: '0644'
    content: |
      [Unit]
      Description=Karetao: set CPU frequency governor to performance
      After=multi-user.target

      [Service]
      Type=oneshot
      ExecStart=/bin/sh -c 'for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > "$g"; done'
      RemainAfterExit=yes

      [Install]
      WantedBy=multi-user.target

  # ROS 2 environment for interactive bash logins. The systemd unit in
  # Part E sources setup.bash explicitly and does not rely on this.
  - path: /etc/profile.d/karetao-ros2.sh
    owner: root:root
    permissions: '0644'
    content: |
      # Karetao: ROS 2 Jazzy environment for interactive bash shells
      if [ -n "$BASH_VERSION" ] && [ -f /opt/ros/jazzy/setup.bash ]; then
        . /opt/ros/jazzy/setup.bash
      fi

  # ROS 2 Jazzy apt source + base packages. Uses the ros2-apt-source
  # package (current ROS 2 documented method); the raw ros.key download
  # used by earlier revisions of this guide is superseded.
  - path: /usr/local/sbin/karetao-install-ros2.sh
    owner: root:root
    permissions: '0755'
    content: |
      #!/bin/bash
      set -euo pipefail
      export DEBIAN_FRONTEND=noninteractive
      add-apt-repository -y universe
      codename="$(. /etc/os-release && echo "${UBUNTU_CODENAME:-${VERSION_CODENAME}}")"
      ver="$(curl -fsSL https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
             | grep -F '"tag_name"' | awk -F'"' '{print $4}')"
      curl -fsSL -o /tmp/ros2-apt-source.deb \
        "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ver}/ros2-apt-source_${ver}.${codename}_all.deb"
      dpkg -i /tmp/ros2-apt-source.deb
      apt-get update
      apt-get install -y \
        ros-jazzy-ros-base \
        ros-dev-tools \
        ros-jazzy-ros2-control \
        ros-jazzy-ros2-controllers \
        ros-jazzy-controller-manager \
        ros-jazzy-joint-state-broadcaster
      echo "ros2-apt-source=${ver}" >> /etc/karetao/provisioning.env

  # Provisioning record, read during acceptance (Part F).
  - path: /etc/karetao/provisioning.env
    owner: root:root
    permissions: '0644'
    content: |
      KARETAO_COMPONENT=RaspberryPi_Sensor_Hub
      KARETAO_PROVISIONING_REV=PROVISIONING_GIT_REV
      KARETAO_TARGET_IMAGE=ubuntu-24.04-preinstalled-server-arm64+raspi

runcmd:
  - [ systemctl, enable, --now, chrony ]
  - [ systemctl, daemon-reload ]
  - [ systemctl, enable, --now, karetao-cpu-governor.service ]
  - [ /usr/local/sbin/karetao-install-ros2.sh ]
  - [ systemctl, restart, ssh ]

final_message: "Karetao Raspberry Sensor Hub host provisioned after $UPTIME seconds. Run 'cloud-init status --long' and Part A9 checks."

# One controlled reboot so the upgraded kernel and groups are in effect.
power_state:
  mode: reboot
  message: "Karetao provisioning complete - rebooting"
  timeout: 60
  condition: true
```

What this seed deliberately leaves to later steps, and why:

| Left out | Reason | Done in |
| --- | --- | --- |
| Ubuntu Pro attach and PREEMPT_RT | Token is a secret; kernel change must be validated, not assumed | Part B |
| SPI overlay check in `config.txt` | Hardware enablement, verified against the actual image | A7 |
| Robot workspace build, systemd unit for the controller | Software source of truth is the ROS workspace, not the seed | Parts D, E |
| SPI, GPIO, latency acceptance | Qualification evidence, not configuration | Parts C, F |
| `isolcpus`, `nohz_full`, IRQ affinity, custom kernel parameters | Premature; a measured baseline comes first | Part F |

## A7. SPI enablement in `config.txt`

While `system-boot` is mounted, check whether the image already enables the SPI controller:

```bash
grep -n "dtparam=spi\|dtoverlay=.*spi" /media/$USER/system-boot/config.txt
```

Ubuntu's official pre-installed Raspberry Pi images ship `dtparam=spi=on` enabled by default in the `[all]` section, so this check should pass without edits. If a future image drops it, add `dtparam=spi=on` under `[all]` and record the change in the provisioning directory. Do not enable additional SPI controllers merely because they exist. The host implementation defaults to **SPI0 CE0**, that is `/dev/spidev0.0` (`RaspberryPi_Sensor_Hub/src/spi/spi_bus.py`).

## A8. Validate, eject, boot

On the workstation:

```bash
cloud-init schema --config-file /media/$USER/system-boot/user-data   # if cloud-init is installed
python3 -c 'import yaml,sys; yaml.safe_load(open(sys.argv[1]))' /media/$USER/system-boot/user-data
python3 -c 'import yaml,sys; yaml.safe_load(open(sys.argv[1]))' /media/$USER/system-boot/network-config
head -1 /media/$USER/system-boot/user-data     # must be exactly "#cloud-config"
grep 'ssh-ed25519' /media/$USER/system-boot/user-data
diff <(grep -o 'ssh-ed25519 .*' /media/$USER/system-boot/user-data) <(cat ~/.ssh/id_ed25519.pub)   # A6.1: must print nothing
sync
udisksctl unmount -b /dev/sdX1
```

Do not proceed if any check fails, and do not proceed if the `diff` prints anything or the placeholder key is still present. A wrong key here is not caught until A9, and by then the only fix is the offline repair in Appendix B.

Insert the card into the powered-off Pi. Connect Ethernet, cooling and power only. **Do not connect the STM32 SPI harness and do not apply motor power.** Power on and allow first boot to complete, including the automatic reboot at the end of provisioning. Do not interrupt power during provisioning. First boot includes a full package upgrade and the ROS 2 install and can take 10 to 20 minutes on a good network.

## A9. Verify provisioning

Find the Pi via the DHCP server or mDNS and connect. If the router's lease list does not show it, try the mDNS name anyway, or find its address with `arp-scan`/`nmap` on the LAN and its MAC (Raspberry Pi OUIs include `d8:3a:dd`, `2c:cf:67`, `dc:a6:32`, `e4:5f:01`); a Pi that answers on the network but is absent from the router's display is normal.

```bash
ssh robot@karetao-pi-01.local
```

On first connection SSH cannot yet know the Pi and asks whether to trust its host key:

```text
The authenticity of host '...' can't be established.
ED25519 key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

This is host-key trust, not the login credential; typing `yes` is normal for a Pi you just provisioned. To verify it rather than trust it blindly, compare the printed fingerprint against the three the Pi generated during first boot, visible from the card before you even connect: `sudo grep -A1 'SHA256:' /mnt/var/log/cloud-init-output.log` (with the `writable` partition mounted at `/mnt`, see Appendix B). A match means you have reached the right Pi.

If the connection instead fails with `Permission denied (publickey)`, the public key placed in `user-data` (A6.1) did not match what the workstation offers, most often because the placeholder was never substituted. See Appendix B to confirm and repair it without a full re-provision.

Then on the Pi:

```bash
cloud-init status --long          # expect: status: done, no errors
sudo cloud-init analyze show
sudo journalctl -u cloud-init -u cloud-final --no-pager | grep -i -E 'error|warn|fail' || true
cat /etc/karetao/provisioning.env
hostnamectl
cat /etc/os-release | grep PRETTY
ip -brief address
id robot                          # expect groups: adm dialout plugdev realtime
sudo sshd -T | grep -E 'passwordauthentication|pubkeyauthentication|permitrootlogin'
ls -l /dev/spidev*                # expect crw-rw---- root dialout ... spidev0.0 (and 0.1)
ls -l /dev/gpiochip*              # expect group dialout on the RP1 chip
ulimit -r; ulimit -l              # expect 99 / unlimited (after a fresh login)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor   # expect performance
chronyc tracking
getent passwd ubuntu || echo "ok: no default ubuntu user"
source /opt/ros/jazzy/setup.bash
ros2 doctor                                              # expect: "All X checks passed"
ros2 doctor --report > /tmp/ros2-doctor-report.txt        # full dump for the record; do not pipe this into head
```

`ros2 doctor --report` prints a very long, unbounded information dump, including every installed package version; it is not itself a pass/fail check. Piping it into `head` or `less -F` can close the pipe while `ros2doctor` is still writing and produce a `BrokenPipeError` traceback. That traceback is a SIGPIPE artefact of the truncation, not a fault on the Pi; ignore it and read the saved file instead. `ros2 doctor` without `--report` is the actual check and is what this step should treat as pass/fail.

**If cloud-init reports an error, stop.** Fix the seed, change `instance-id`, and re-provision. Do not hand-repair and continue; the point of the seed is reproducibility.

Only create a separate maintenance account if required, and if it is required on every Pi, move it into `user-data` under version control.

## A10. Optional Wi-Fi fallback for commissioning

Ethernet remains the required commissioning network (A2) and the only network cloud-init configures (A6.3). This step exists only for sites where a wired drop genuinely is not available during commissioning. It is a manual, on-box fallback, not a repeatable provisioning input, and it is deliberately **not** added to the cloud-init seed:

* It carries a Wi-Fi passphrase, and G3 forbids putting secrets in version control, where the seed lives.
* A2's Ethernet requirement and A4's instruction to decline Wi-Fi in the Imager are both about what gets *provisioned*; this step runs after provisioning is already done and verified, so it does not contradict them.
* Do not attempt this step until A9 has passed cleanly over Ethernet. Configuring Wi-Fi is the first thing done *through* a confirmed-working headless SSH session, never a substitute for reaching that point.

**Every step below runs on the Pi itself, inside the SSH session from A9.** Unlike A5–A8, there is no SD card to remount and no file to edit on the workstation (laptop) — the card is already sealed inside a running Pi. The workstation's only role in A10 is the terminal you're typing into; the `ssh` connection carries every command through to the Pi, and every file this step creates lives on the Pi's own root filesystem (`/etc/netplan/`), not on `system-boot`.

**1. On the Pi — confirm the wireless interface and tooling.** Still connected over Ethernet from A9:

```bash
ip link show                                  # confirm the onboard wireless interface name, typically wlan0
sudo apt list --installed 2>/dev/null | grep -E 'netplan|wpasupplicant'   # both ship on the base image
```

**2. On the Pi — turn the Wi-Fi passphrase into a PSK hash.** Ubuntu Server's Raspberry Pi image uses netplan with the `networkd` renderer, not NetworkManager, so Wi-Fi is configured as a second netplan file placed directly on the Pi's running system, alongside the one cloud-init already wrote there during A6/A8. `wpa_passphrase` derives the hash so the plaintext password never lands in a file:

```bash
wpa_passphrase 'YOUR_SSID' 'YOUR_PASSPHRASE'   # prints a psk=<hex> line; copy that hash, not the plaintext, for step 3
```

**3. On the Pi — write and apply the netplan file.** Paste the `psk=` hash from step 2 into the placeholder below:

```bash
sudo tee /etc/netplan/60-wifi-fallback.yaml > /dev/null <<'EOF'
network:
  version: 2
  wifis:
    wlan0:
      regulatory-domain: "NZ"
      optional: true
      access-points:
        "YOUR_SSID":
          password: "PASTE_THE_psk_HEX_HERE"
      dhcp4: true
      dhcp4-overrides:
        route-metric: 200        # keep Ethernet preferred while both links are up
EOF
sudo chmod 600 /etc/netplan/60-wifi-fallback.yaml
sudo chown root:root /etc/netplan/60-wifi-fallback.yaml
sudo netplan generate
sudo netplan apply
```

`route-metric: 200` keeps `eth0` (cloud-init's default metric) preferred whenever both links are up, so this file adds a fallback rather than silently switching the Pi's traffic path.

**4. On the Pi — verify Wi-Fi associated and Ethernet is still preferred.** Do this before touching the Ethernet cable:

```bash
ip -brief address show wlan0                  # expect an IPv4 address once associated
ip route                                       # expect the eth0 default route to sort first (lower metric)
iw dev wlan0 link                              # signal and associated AP, for the record
```

**5. On the Pi (physically) and from the workstation — cut over and confirm.** Only after step 4 shows both interfaces with addresses and the SSH session still reachable should the Ethernet cable be pulled. Pulling the cable is the one physical action in this step and happens at the Pi; reconnecting is a normal `ssh` from wherever you're working, exactly as in A9, and confirms the session survives the switch:

```bash
ssh robot@karetao-pi-01.local
```

**6. Record and, later, clean up.** Note in commissioning records (not in `user-data`, and not on the Pi at all) that this Pi ran part of commissioning over Wi-Fi, and re-confirm Ethernet on a wired drop before signing off F4 acceptance; Part F's timing and latency evidence should not be collected over Wi-Fi. Once commissioning is complete, on the Pi either remove the fallback file or leave it in place:

```bash
sudo rm /etc/netplan/60-wifi-fallback.yaml && sudo netplan apply   # remove, or skip this to keep it as a standing fallback
```

Leaving it in place does not affect the deployed robot's network path as long as Ethernet keeps the lower route metric.

---

# Part B — Real-time kernel and governor

## B1. Ubuntu PREEMPT_RT via Ubuntu Pro

Ubuntu's real-time kernel for Raspberry Pi 4 and 5 is delivered through Ubuntu Pro. Obtain the token separately. **Never place the token in `user-data` or source control.**

```bash
sudo pro attach                                   # prompts for the token
sudo pro enable realtime-kernel --variant=raspi
sudo reboot
```

After reboot:

```bash
uname -r                    # expect a -raspi-realtime kernel
cat /sys/kernel/realtime    # must print 1
pro status
```

If `/sys/kernel/realtime` is not `1`, stop and inspect `sudo journalctl -b -k`. Do not continue assuming PREEMPT_RT is active. Keep the standard `-raspi` kernel installed as a recovery option until the complete hardware test plan has passed.

## B2. Real-time permissions

Already provisioned by cloud-init (`realtime` group, limits file). Verify after a fresh login:

```bash
id | grep -o realtime
ulimit -r     # 99
ulimit -l     # unlimited
```

Do not grant real-time scheduling to general-purpose users.

## B3. CPU governor

Already set to `performance` by `karetao-cpu-governor.service`. Verify:

```bash
systemctl status karetao-cpu-governor.service --no-pager
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

Do **not** yet introduce `isolcpus`, `nohz_full`, `rcu_nocbs`, IRQ pinning or other kernel command-line parameters. Establish the Part F baseline first; premature isolation can make latency worse.

---

# Part C — Time authority

The Raspberry Pi is the system time authority (SPI_SYSTEM_INTERFACE §10, TIME_SYSTEM_INTERFACE §1). chrony is enabled by cloud-init. Check:

```bash
timedatectl status
chronyc tracking
chronyc sources -v
```

Two points that follow from the contracts and are **open component decisions**, to be settled in the host implementation before TIME_SYNC validation:

1. **Which Pi clock feeds `pi_time_us`.** The contract defines `pi_time_us` as Pi time at the synchronization point but does not name a clock. If `CLOCK_REALTIME` is used, an NTP step on the Pi becomes an offset jump at the STM32, which the runtime bound of ±1 s (SD-21) will reject. Either use a monotonic clock as the exported domain or ensure chrony only slews after initial sync (chrony's default `makestep 1 3` steps only during the first three updates).
2. **Drift budget.** SD-19 requires measuring whether drift between 1 Hz syncs stays inside the ±1 ms target (SD-18). That is an integration measurement, not a provisioning setting.

Do not begin STM32 TIME_SYNC validation until `chronyc tracking` shows a synchronized source and the clock-source decision above has been recorded.

---

# Part D — ROS 2 workspace

ROS 2 Jazzy (`ros-base`, `ros2_control`, `controller_manager`, `joint_state_broadcaster`) is installed by cloud-init. Do not re-add the apt source by hand; if the install failed, fix the seed and re-provision.

## D1. Clone the Karetao repository

The Karetao repository contains the system contracts (`Documentation/`), the STM32 firmware (`Arm_Sensor_Hub/`), and the Raspberry Pi host packages (`RaspberryPi_Sensor_Hub/`). Clone it to a working directory as `robot`:

```bash
cd ~
git clone https://github.com/karetao/karetao.git          # or your fork URL
cd karetao
git log -1 --oneline                                       # confirm the commit you're running
```

Alternatively, if the repository is deployed offline (e.g., copied onto the card before first boot), ensure it is owned by `robot`:

```bash
sudo chown -R robot:robot ~/karetao
```

**Keep the full Karetao repository under version control.** Do not modify files under `Documentation/` or `Arm_Sensor_Hub/` on the Pi; those are read-only reference and firmware source. Local changes belong in the ROS workspace and in deployment/commissioning records kept outside the repo (G3).

## D2. Create and build the ROS 2 workspace

Create the workspace and link the Raspberry Sensor Hub packages:

```bash
mkdir -p ~/karetao_ws/src
cd ~/karetao_ws

# Link the Raspberry Sensor Hub component into the workspace
ln -s ~/karetao/RaspberryPi_Sensor_Hub ~/karetao_ws/src/

# (Optional) If you have other ROS packages (e.g. control, perception), link them here too
# ln -s ~/karetao/path/to/other_package ~/karetao_ws/src/

# Build with symlink-install so edits take effect without rebuild
colcon build --symlink-install

# Add the workspace setup to the login shell
echo 'source ~/karetao_ws/install/setup.bash' >> ~/.bashrc
```

If the build fails, check that:
- `apt install python3-colcon-common-extensions` (should be in the cloud-init seed)
- ROS 2 Jazzy is installed and sourced: `source /opt/ros/jazzy/setup.bash`
- All `rosdep` dependencies are satisfied: `rosdep install --from-paths src --ignore-src -y`

## D3. Verify the workspace

Confirm that the workspace installed correctly:

```bash
source ~/karetao_ws/install/setup.bash
ros2 pkg list | grep karetao                              # should list the installed packages
ros2 launch karetao_bringup --show-args hardware_inactive.launch.py 2>/dev/null | head -5  # check launch file exists
```

Keep all project software under version control. Do not modify anything under `/opt/ros`. Workspace builds are local (`build/` and `install/` directories); do not commit them.

---

# Part E — SPI and GPIO host bring-up

## E1. Frozen system values

These are Karetao decisions and are **not** re-decided in harness documentation:

| Item | Value | Source |
| --- | --- | --- |
| SPI mode | Mode 0 (CPOL=0, CPHA=0) | SYS-SPI-001 |
| Transaction | Fixed 512 bytes, max 490-byte payload | SYS-SPI-001 |
| Byte order / integrity | Little-endian, CRC-32/ISO-HDLC | SYS-SPI-001 |
| Clock | 5 MHz **initial maximum**, not hardware approval | SYS-TIM-003 |
| Ownership | Pipelined request/response; Pi initiates all clocking | SPI_SYSTEM_INTERFACE §4 |
| DATA_READY | Optional notification; 1 ms polling is the recovery path and, today, the only path | SYS-SPI-003, SD-17 |
| Host-stall timeout | 100 ms (STM32 side) | SPI_SYSTEM_INTERFACE §7 |
| Cable | 20 to 30 cm | SYS-SPI-004 |

What the harness documentation **does** need to freeze, because it is not yet fixed anywhere:

* Pi SPI controller and chip select actually used (implementation default SPI0 CE0, `/dev/spidev0.0`; header pins 19 MOSI, 21 MISO, 23 SCLK, 24 CE0).
* Pi GPIO for DATA_READY. **Harness assignment: GPIO25** (BCM numbering), `gpiochip4` line 25 on the Ubuntu 24.04 kernel, physical header pin 22, wired on the current test rig (confirmed against a live `gpioinfo gpiochip4` dump on this board). Request it via libgpiod as an input, rising-edge, Schmitt trigger enabled, no internal pull, since the STM32 drives the line push-pull (`ARM_SENSOR_HUB.md`, RP1 peripherals datasheet §3.1.3). **This is a harness assignment, not a validated one.** SD-17 (register §3.2) is satisfied by picking and wiring an available pin; it is not closed until the electrical and timing acceptance in `SPI_SYSTEM_INTERFACE.md` §16 has been performed on the actual wiring. Until that acceptance is recorded, the host continues to run polling-only at 1 ms and the achieved latency and jitter must still be measured, not assumed.
* Pin-to-pin mapping against the STM32 side: NSS PA15, SCK PC10, MISO PC11, MOSI PC12, DATA_READY PA8 ↔ Pi GPIO25 (assigned, pending electrical validation) (`ARM_SENSOR_HUB.md`).

## E2. Inspect the Pi side

`robot`'s membership in `dialout` gives ordinary access to `spidev*` and to the RP1 GPIO chip specifically (Ubuntu's udev rules grant `0660` group ownership of these device nodes; see A9, A6.4). That access is scoped to the RP1 chip only, not to every GPIO controller on the board:

```bash
ls -l /dev/spidev*                 # expect /dev/spidev0.0, group dialout
sudo gpiodetect                     # enumerates *every* /dev/gpiochip*; needs root
gpioinfo gpiochip4 | head -60       # the RP1 chip only; robot needs no sudo here
```

`gpiodetect` opens every `gpiochip*` device to list it, including `gpiochip0`–`3`, which belong to other on-SoC controllers (`gpio-brcmstb`) and are intentionally `root:root`, not `dialout`. As `robot`, `gpiodetect` therefore fails with `Permission denied` even though the RP1 chip itself is fully accessible; that is expected, not a permissions defect. Use `sudo` for `gpiodetect` when discovering the chip layout, and `gpioinfo <chip>` without `sudo` once the target chip is known, since it only opens that one device.

If `gpioinfo gpiochip4` itself fails as `robot`, *that* is a real permissions defect: re-login to pick up a group change made after the current session started, or confirm the running kernel's GPIO driver is still `pinctrl-rp1` (`sudo gpiodetect`, and E2's numbering table below), since a driver rename would make the udev rule stop matching that chip.

GPIO chip numbering on the Pi 5 depends on the kernel:

| Kernel | 40-pin header chip | Line numbering | sysfs base |
| --- | --- | --- | --- |
| Ubuntu 24.04 (6.8 raspi) | `gpiochip4` (RP1) | line = BCM number, 0 to 53 | 571, so BCM 24 is global 595 |
| Newer kernels (later Raspberry Pi OS, Ubuntu 26.04) | `gpiochip0` | line = BCM number | changes |

Because of this, the host software must **not** hard-code a chip number. Select the chip by its label or driver (`pinctrl-rp1`) via libgpiod, or hold the chip path in configuration and re-verify with `sudo gpiodetect` after every kernel change (a controlled change, G2). If GPIO requests fail after an upgrade with `gpiochip4`, the chip has most likely become `gpiochip0`.

Use libgpiod for GPIO. Do not use the deprecated sysfs GPIO interface or its global line numbers. The DATA_READY GPIO assignment is GPIO25 (E1); request it as an input with rising-edge events, Schmitt trigger enabled, and no internal pull.

## E3. Connect the STM32

Power off both boards. Connect the SPI harness and verify: common ground, 3.3 V-only signalling, SCK/MOSI/MISO/NSS directions, DATA_READY (GPIO25, assigned and wired), 20 to 30 cm cable, no back-powering, STM32 reset and power state. **Motor power stays removed.**

## E4. Initial transport validation

Start below the ceiling, then step up. The implementation default is 5 MHz (`SpiBusConfig.max_speed_hz`); override it lower for the first transactions.

Suggested sequence: 1 MHz → 2 MHz → 5 MHz, each with a soak run, logging CRC failures, sequence gaps and NACKs.

Test only these message types first: `GET_STATUS`, `GET_SNAPSHOT`, `GET_VERSION`, `TIME_SYNC`. Do not send `SET_MOTOR_COMMAND` to prove the link works; its payload is not frozen (SPI_PAYLOAD_SCHEMA).

The host must, before accepting any frame, validate magic, protocol version, length, CRC32 and sequence, reject stale or duplicate responses, and never use SPI reception time as measurement time (SPI_SYSTEM_INTERFACE §13). The current `spi_device.py` provides only stateless `transact` and `get_status` helpers; outstanding-transaction tracking is still to be written (register §3.5).

Record for the SPI integration gate: DMA/NSS behaviour under a real master, DATA_READY electrical timing if wired, SCK/MISO signal integrity at 5 MHz, sustained 512-byte transactions, request/response correlation, host-stall recovery, and the cable length used.

---

# Part F — Controller runtime and acceptance

## F1. ros2_control safety defaults

The controller manager must not activate physical hardware at boot; hardware starts `inactive` and requires explicit activation (SYS-REC-002, SYSTEM_LIFECYCLE §2, §5).

```yaml
controller_manager:
  ros__parameters:
    update_rate: 100                      # SYS-TIM-001 baseline; final rate from measurement
    enforce_command_limits: true
    hardware_components_initial_state:
      inactive:
        - karetao_arm_hardware
      shutdown_on_initial_state_failure: true
    defaults:
      allow_controller_activation_with_inactive_hardware: false
      deactivate_controllers_on_hardware_self_deactivate: true
```

Initial real-time settings: `lock_memory: true`, `thread_priority: 50`. No CPU affinity until F3 identifies a suitable CPU. Invalid, stale or unsynchronized records must become faults, not inputs (SYS-SYNC-003, SYSTEM_SYNCHRONIZATION integration obligations). The EKF must not bypass the STM32 command gate.

## F2. Managed systemd service

Do not run the robot host from an SSH shell in deployment. Unit at `/etc/systemd/system/karetao-host.service` (also version-controlled under `provisioning/systemd/`):

```ini
[Unit]
Description=Karetao Raspberry Sensor Hub host (hardware starts inactive)
After=network-online.target chrony.service
Wants=network-online.target

[Service]
Type=simple
User=robot
Group=robot
WorkingDirectory=/home/robot/karetao_ws
Environment=ROS_DOMAIN_ID=0
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && source /home/robot/karetao_ws/install/setup.bash && exec ros2 launch karetao_bringup hardware_inactive.launch.py'
Restart=on-failure
RestartSec=2
LimitRTPRIO=99
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
```

Replace the package and launch file names with the real ones. `Restart=on-failure` is acceptable only because the launch file leaves hardware `inactive`; a restart must never itself resume motion (SYS-REC-002).

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now karetao-host.service
sudo systemctl status karetao-host.service --no-pager
sudo journalctl -u karetao-host.service -b -f
```

## F3. Real-time measurement

Idle and loaded baselines on the RT kernel:

```bash
sudo cyclictest --smp -p95 -m -i200 -h400 -q -D 300s
# second session
stress-ng --cpu 3 --io 2 --vm 1 --vm-bytes 512M --timeout 300s --metrics-brief
```

Record max and average latency, kernel version, governor, temperature, active services and duration. Repeat with ROS running, SPI traffic, logging and network load. Derive the latency budget from the 100 Hz controller period and the SPI transaction deadline. Judge by maximum, not average.

Verify scheduling of the running controller:

```bash
ps -eLo pid,tid,cls,rtprio,pri,psr,comm | grep -E 'ros2_control|controller_manager'
grep -E 'VmLck|CapEff' /proc/$(pgrep -o ros2_control_node)/status
```

## F4. Acceptance sequence

Complete in order. A failure returns the system to the previous safe stage. Results are **component evidence**; only Karetao's verification process assigns `SYSTEM_VERIFIED` (SYSTEM_VERIFICATION_MATRIX).

| Stage | Verify | Karetao reference |
| --- | --- | --- |
| F4.1 Provisioning | `cloud-init status` done, no errors; A9 checks pass; provisioning revision recorded | this document |
| F4.2 OS | SSH key-only login, Ubuntu 24.04, RT kernel active, chrony synchronized | Part B, C |
| F4.3 Permissions | `robot` in `realtime`, `dialout`; rtprio 99; memlock unlimited; spidev and the RP1 gpiochip accessible; chip number recorded for the running kernel | Part B2, E2 |
| F4.4 Thermal / power | No undervoltage or throttling under representative load (`vcgencmd get_throttled` if available) | — |
| F4.5 SPI electrical | Logic analyser: levels, pin map, CPOL/CPHA = Mode 0, CS, DATA_READY if wired, timing at 1/2/5 MHz, cable length | SYS-SPI-001, SYS-TIM-003, SYS-SPI-004 |
| F4.6 SPI protocol | Status, snapshot, version, TIME_SYNC frames; CRC; sequence; stale rejection; STM32 reset recovery; host restart recovery | SYS-SPI-001/002/003 |
| F4.7 Time sync | TIME_SYNC at 1 Hz accepted; validity expires after 5 s without update; implausible offsets rejected; clock-source decision recorded | SYS-SYNC-001 to 005 |
| F4.8 Fault behaviour | SPI disconnect, TIME_SYNC interruption, malformed and stale frames, STM32 reset, Pi restart, **heartbeat loss (500 ms)**: no unsafe command accepted, no last-command hold | SYS-FAIL-001/002, SYS-REC-001/002 |
| F4.9 ROS lifecycle | Hardware starts inactive; activation requires healthy transport and valid sync; faults propagate; controllers deactivate on hardware self-deactivate | SYSTEM_LIFECYCLE §2, §5, §9 |
| F4.10 Motion release | **Not covered by this guide.** Requires release conditions 1 to 7 and SAFE-001 to SAFE-009, independently reviewed | Register Part 4, SAFETY_REQUIREMENTS |

Open item affecting F4.8: the SPI message set (SPI_SYSTEM_INTERFACE §5) does not yet define a heartbeat carrier, and command acknowledgement and freshness semantics remain open (HOST_SYSTEM_INTERFACE). Test heartbeat loss once the carrier is defined; do not invent one here.

---

# Part G — Reproducibility and operations

## G1. Provisioning layout

Provisioning and versioning are split across the repository and the ROS workspace. Contracts are **not** duplicated; they stay in Karetao `Documentation/02_INTERFACES/`.

**On the Pi at runtime:**

```text
/home/robot/
├── karetao/                      # full Karetao repository (git clone)
│   ├── Documentation/            # system contracts, read-only reference
│   ├── Arm_Sensor_Hub/           # STM32 firmware, read-only reference
│   └── RaspberryPi_Sensor_Hub/   # component authority, read-only reference
│       ├── provisioning/
│       │   ├── cloud-init/
│       │   │   ├── meta-data
│       │   │   ├── network-config
│       │   │   └── user-data
│       │   ├── systemd/
│       │   │   └── karetao-host.service
│       │   └── README.md         # image version, config.txt deltas, harness pin table
│       ├── src/                  # host software (Python SPI stack, ROS packages)
│       ├── tests/
│       └── Documentation/
│           └── RASPBERRY_PI_BRINGUP_V1.md   # this file
│
└── karetao_ws/                   # ROS 2 workspace (local build)
    ├── src/
    │   └── RaspberryPi_Sensor_Hub -> ../../karetao/RaspberryPi_Sensor_Hub (symlink)
    ├── build/                    # local, not version-controlled
    ├── install/                  # local, not version-controlled
    └── ...
```

Source-of-truth split:

* **System contracts and requirements:** Karetao `Documentation/` (read-only reference)
* **Firmware source:** Karetao `Arm_Sensor_Hub/` (read-only reference)
* **Machine provisioning:** `provisioning/cloud-init/` (version-controlled seed)
* **Host software:** Karetao `RaspberryPi_Sensor_Hub/src/` (version-controlled source)
* **ROS workspace:** `~/karetao_ws/` (local build, not version-controlled)
* **Motion release:** Karetao `04_SAFETY/` and the register's release conditions
* **Deployment records:** separate from version control (commissioning, calibration, evidence)

## G2. Controlled changes

Treat these as controlled changes requiring fresh timing and integration evidence: SPI overlays and pin assignments, DATA_READY GPIO assignment, SPI clock, kernel version or parameters, controller update rate, CPU affinity, RT priority, cloud-init seed, hardware interface configuration.

## G3. Operations

* Apply OS and ROS updates in a maintenance window; after kernel changes re-run RT, SPI, latency, lifecycle and safety acceptance.
* Keep a known-good image, the seed, and the offline key-recovery procedure (Appendix B) as the documented recovery route.
* Monitor journal, clock sync, storage, temperature, throttling, controller-manager and SPI diagnostics.
* Back up the ROS workspace, systemd units, hardware configuration, calibration records (host-side source copy, SYS-CAL-002), deployment records and the seed.
* Never commit private keys, Ubuntu Pro tokens, passwords or other secrets.

---

# Appendix A — Conflict review resolved in this revision (2026-09-20)

Findings from checking the previous text of this guide against `Documentation/01_SYSTEM`, `02_INTERFACES`, `03_COMPONENTS`, `04_SAFETY` and the decisions register.

| # | Previous text | Conflict | Resolution |
| --- | --- | --- | --- |
| 1 | References to `SPI_CONTRACT.md`, `LIFECYCLE_CONTRACT.md`, `SAFETY_RELEASE_CHECKLIST.md` | Legacy `docs/project` names; not current authority. Checklist is archived and non-normative | Replaced with Karetao `Documentation/**` paths and SAFE-/SYS- identifiers |
| 2 | Proposed `contracts/` directory holding SPI/lifecycle contracts inside the component tree | Component documentation must not establish a competing authority (DOCUMENTATION_AUTHORITY_MODEL) | Contracts referenced, not copied; layout revised (G1) |
| 3 | "The STM32 remains the final safety authority" | SD-25: STM32/Pi controls are supplementary only; motion-permission authority is an open decision (SD-02) | Statement removed; roles section rewritten |
| 4 | Pi host named after the STM32 component (`arm_sensor_hub_ws`, `arm-sensor-hub.service`, `arm_sensor_hub` hardware component, "Arm Sensor Hub Control") | The Pi hosts the Raspberry Sensor Hub; the Arm Sensor Hub is the STM32 (03_COMPONENTS) | Renamed to `karetao-*` identifiers |
| 5 | "Freeze SPI mode and maximum clock in harness documentation" | Mode 0 and the 5 MHz ceiling are Karetao decisions (SYS-SPI-001, SYS-TIM-003) | Listed as frozen values; harness freezes only Pi-side pins and the DATA_READY GPIO |
| 6 | DATA_READY treated as an existing GPIO to configure | No Pi GPIO is assigned (SD-17); polling at 1 ms is the only current path | Stated explicitly; polling-only latency measurement required |
| 7 | No mention of SPI cable length | SYS-SPI-004 requires 20 to 30 cm and measurement over that length | Added to hardware, connection and acceptance steps |
| 8 | Fault tests omitted heartbeat loss | SYS-FAIL-001/002 (500 ms heartbeat timeout, no last-command hold) | Added to F4.8, with the open heartbeat-carrier item flagged |
| 9 | Acceptance sequence presented as sufficient qualification | Component evidence is not system verification (SYSTEM_VERIFICATION_MATRIX) | Stated in F4; motion release deferred to Karetao gates |
| 10 | cloud-init set `en_NZ.UTF-8` then ROS step forced `en_US.UTF-8` | Internal inconsistency | Single locale in the seed |
| 11 | ROS apt source via raw `ros.key` download | Superseded by the `ros2-apt-source` package in current ROS 2 documentation | Seed installs `ros2-apt-source` |
| 12 | RT limits, governor, ROS install done by hand after boot | Contradicted the guide's own principle that cloud-init owns repeatable provisioning | Moved into `user-data` |
| 13 | `-a3` affinity in cyclictest alongside "no affinity yet" | Minor internal inconsistency | Affinity flag removed from the baseline run |
| 14 | No console recovery despite key-only, password-locked login | Guide's own operations section demands a recovery method, but a locked-password console cannot log in either | Documented the actual recovery route: offline repair of `authorized_keys` on the card (Appendix B), added key-substitution verification at A6.1/A8 to catch the fault before boot |

Observations recorded but **not** resolvable here because they are component or system decisions still open: clock source for `pi_time_us` and NTP step interaction with SD-21 (Part C); heartbeat carrier and acknowledgement semantics (F4); outstanding-transaction tracking in `spi_device.py` (E4).

---

# Appendix B — Recovering a Pi with a bad or missing SSH key

This is the recovery path when A9's SSH connection fails with `Permission denied (publickey)`, meaning the key baked into `user-data` at A6.1 was wrong. Because password login is disabled (`ssh_pwauth: false`) and the account password is locked (`lock_passwd: true`), there is no in-band way to log in and fix this. The only writable path to the account is the card itself, so this requires powering the Pi down.

Powering off an idle Pi at a login prompt is safe; ext4 journaling handles the unclean stop, and re-provisioning is not needed because cloud-init has already run and will not repeat its user setup for the same `instance-id`.

1. **Power off the Pi**, remove the card, and mount its second partition (`writable`, not `system-boot`) on the workstation:

   ```bash
   lsblk -o NAME,SIZE,LABEL         # confirm which is writable, e.g. /dev/sdb2
   sudo mount /dev/sdb2 /mnt
   ```

2. **Confirm the fault** by reading what actually landed in `authorized_keys`:

   ```bash
   sudo cat /mnt/home/robot/.ssh/authorized_keys
   ```

   Comparing this against `cat ~/.ssh/id_ed25519.pub` on the workstation shows whether it is the unresolved placeholder, a mistyped key, or genuinely a different key than the one being offered.

3. **Write the correct key** and restore ownership and permissions:

   ```bash
   grep '^robot:' /mnt/etc/passwd                    # confirm the uid, normally 1000
   sudo tee /mnt/home/robot/.ssh/authorized_keys < ~/.ssh/id_ed25519.pub
   sudo chown -R 1000:1000 /mnt/home/robot/.ssh       # use the uid from passwd if different
   sudo chmod 700 /mnt/home/robot/.ssh
   sudo chmod 600 /mnt/home/robot/.ssh/authorized_keys
   sudo cat /mnt/home/robot/.ssh/authorized_keys      # should now print your key, in full
   ```

4. **Unmount cleanly** and reboot the Pi:

   ```bash
   sudo umount /mnt
   ```

   Then `ssh robot@karetao-pi-01.local` should succeed without a password.

5. **Fix the source of truth.** Correct the same key in `RaspberryPi_Sensor_Hub/provisioning/cloud-init/user-data` under version control (A6.1), so the next card written from this seed does not repeat the fault. This step alone does not fix the Pi that is already provisioned; step 3 does.

Do not add a console-login password to `user-data` as an alternative recovery route: it would put a password hash in version control, which A6 and G3 both forbid. This offline-repair procedure is the documented recovery method referred to in G3's "keep a recovery procedure."