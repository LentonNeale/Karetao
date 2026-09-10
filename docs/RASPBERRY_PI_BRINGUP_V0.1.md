# Raspberry Pi 5 Bring-Up Guide

## Ubuntu Server 24.04 LTS, cloud-init, PREEMPT_RT, ROS 2 and STM32 Host

This procedure provisions a Raspberry Pi 5 (8 GB) as the Linux host for the Arm Sensor Hub.

The Pi provides:

* ROS 2 execution
* SPI master functionality
* system-time authority
* high-level control and estimation
* host-side diagnostics
* communication with the STM32

The STM32 remains responsible for:

* sensor acquisition
* CAN transport
* low-level lifecycle enforcement
* command validation
* safe command rejection

**Do not energize motors until the hardware and acceptance sections are complete.**

See:

* `SPI_CONTRACT.md`
* `LIFECYCLE_CONTRACT.md`
* `SAFETY_RELEASE_CHECKLIST.md`

before connecting an energized system.

---

# 1. Provisioning Strategy

The Raspberry Pi is provisioned in two distinct stages.

### Stage 1 — Operating-system imaging

Raspberry Pi Imager is used only to write the official Ubuntu Server image to the SD card.

**No Raspberry Pi Imager advanced/customisation settings are used.**

The Imager is therefore responsible only for:

```text
Ubuntu Server 24.04 LTS arm64
        ↓
SD card
```

### Stage 2 — First-boot configuration

After imaging, the SD card's Ubuntu boot partition is mounted on the workstation.

The existing cloud-init configuration is then edited:

```text
meta-data
network-config
user-data
```

On Ubuntu Raspberry Pi images, these files form the cloud-init seed and are located on the boot partition. Canonical explicitly documents customising this configuration before first boot.

The resulting workflow is:

```text
┌──────────────────────────┐
│ Raspberry Pi Imager      │
│                          │
│ Ubuntu Server 24.04 LTS  │
└────────────┬─────────────┘
             │
             ▼
      Write SD card
             │
             ▼
┌──────────────────────────┐
│ Mount boot partition     │
│                          │
│ Configure cloud-init:    │
│  user-data               │
│  network-config          │
│  meta-data               │
└────────────┬─────────────┘
             │
             ▼
       Insert SD card
             │
             ▼
┌──────────────────────────┐
│ Raspberry Pi 5           │
│                          │
│ Ubuntu first boot        │
│          ↓               │
│ cloud-init               │
│          ↓               │
│ Provisioned system       │
└──────────────────────────┘
```

This keeps the OS image generic and makes the project-specific configuration reproducible.

---

# 2. Prepare Hardware

Obtain:

* Raspberry Pi 5, 8 GB
* Official 27 W USB-C power supply
* Active cooler
* Reliable 32 GB or larger high-endurance microSD card for commissioning
* SSD or other robust boot media for a deployed robot
* Wired Ethernet
* DHCP-enabled network
* Dedicated 3.3 V SPI connection between Pi and STM32
* Common ground between Pi and STM32
* Separate emergency-stop/power-interlock path

**Neither Linux nor the SPI link is an emergency stop.**

Before first boot, update the Pi bootloader EEPROM if required.

Do not interrupt power during an EEPROM update.

For commissioning, use Ethernet rather than Wi-Fi wherever practical.

---

# 3. Install Raspberry Pi Imager

On the workstation:

```bash
sudo snap install rpi-imager
```

Launch:

```bash
rpi-imager
```

Ubuntu documents Raspberry Pi Imager as the standard method for writing Ubuntu images to Raspberry Pi storage.

---

# 4. Write the Ubuntu Server Image

In Raspberry Pi Imager:

### Device

Select:

```text
Raspberry Pi 5
```

### Operating System

Select:

```text
Ubuntu
    ↓
Ubuntu Server 24.04 LTS
    ↓
64-bit
```

### Storage

Select the intended SD card.

**Verify the storage device carefully.**

Writing the image erases the selected device.

### Raspberry Pi Imager customisation

When Raspberry Pi Imager offers OS customisation or advanced settings:

**Do not configure anything.**

Do not enter:

* hostname
* username
* password
* SSH credentials
* Wi-Fi configuration
* locale
* timezone
* keyboard
* other advanced settings

The project uses cloud-init for this configuration instead.

This separation is intentional.

Raspberry Pi Imager writes the OS; cloud-init provisions the machine. Ubuntu's current Raspberry Pi documentation supports customising the cloud-init seed on the boot partition before first boot.

Write the image.

Allow Raspberry Pi Imager to complete its verification.

Do not boot the Pi yet.

---

# 5. Reinsert the SD Card and Locate the Boot Partition

After Raspberry Pi Imager completes:

1. Safely eject the SD card.
2. Remove it from the reader.
3. Reinsert it.

The Ubuntu image contains a boot partition formatted for access from the workstation.

Ubuntu documents this partition as the location of the Raspberry Pi cloud-init seed.

On Linux, identify the partitions:

```bash
lsblk
```

You should see the SD card and its partitions.

For example:

```text
mmcblk0
├── mmcblk0p1
└── mmcblk0p2
```

The first partition is the boot partition.

Mount it if the desktop environment has not already mounted it.

For example:

```bash
udisksctl mount -b /dev/sdX1
```

Replace `/dev/sdX1` with the actual boot partition.

**Do not guess the device name.**

Confirm the contents:

```bash
ls -la /media/$USER/
```

The Ubuntu Raspberry Pi image should contain the cloud-init configuration on this partition.

Typical files include:

```text
meta-data
network-config
user-data
```

Ubuntu documents these three files as the cloud-init configuration used by the Raspberry Pi image.

---

# 6. Configure `meta-data`

Open the existing:

```text
meta-data
```

Do not unnecessarily replace the entire file if the Ubuntu image already provides a valid configuration.

For a dedicated deployment, ensure the instance has a unique identity.

Example:

```yaml
instance-id: arm-pi-01
local-hostname: arm-pi-01
```

For another Pi:

```yaml
instance-id: arm-pi-02
local-hostname: arm-pi-02
```

The hostname should be DNS-safe and unique within the deployment environment.

---

# 7. Configure `network-config`

For the commissioning system, use Ethernet with DHCP.

Example:

```yaml
version: 2

ethernets:
  eth0:
    dhcp4: true
```

However, **do not assume the interface is named `eth0` without checking the image's existing configuration**.

If the existing Ubuntu image already contains a valid network configuration, preserve it unless there is a reason to change it.

For this project:

```text
Ethernet
   ↓
DHCP
   ↓
Pi IP address
   ↓
SSH
```

is preferred during commissioning.

Do not introduce static IP configuration unless the deployment architecture requires it.

---

# 8. Configure `user-data`

This is the primary cloud-init configuration.

Open:

```text
user-data
```

The file must begin with:

```yaml
#cloud-config
```

The project-specific configuration should provision the base machine.

A suitable starting point is:

```yaml
#cloud-config

hostname: arm-pi-01
manage_etc_hosts: true

users:
  - name: robot
    gecos: Arm Sensor Hub Control
    shell: /bin/bash
    lock_passwd: true
    groups:
      - adm
      - dialout
    sudo:
      - "ALL=(ALL) NOPASSWD:ALL"
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...REPLACE_WITH_PUBLIC_KEY...

ssh_pwauth: false

package_update: true
package_upgrade: true

packages:
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
  - chrony
  - ethtool
  - htop
  - i2c-tools
  - spi-tools
  - gpiod
  - stress-ng
  - rt-tests

timezone: Pacific/Auckland

locale: en_NZ.UTF-8

write_files:

  - path: /etc/ssh/sshd_config.d/10-arm-sensor-hub.conf
    permissions: '0644'
    owner: root:root
    content: |
      PermitRootLogin no
      PasswordAuthentication no
      KbdInteractiveAuthentication no
      PubkeyAuthentication yes
      AllowUsers robot

runcmd:

  - systemctl enable chrony
  - systemctl restart chrony
```

Replace:

```text
ssh-ed25519 AAAA...REPLACE_WITH_PUBLIC_KEY...
```

with the actual **public** SSH key.

Never place the private SSH key in:

* `user-data`
* the SD card
* the repository
* the Pi image

---

# 9. Cloud-Init Configuration Principles

The cloud-init configuration should contain **repeatable machine provisioning**, not secrets or one-off hardware test actions.

Good candidates for cloud-init:

```text
hostname
users
SSH keys
package installation
locale
timezone
base configuration
system configuration
persistent configuration files
basic services
```

Avoid putting the following directly into initial cloud-init unless there is a compelling reason:

```text
Ubuntu Pro credentials
private SSH keys
hardware acceptance tests
SPI validation
motor commands
calibration data
deployment-specific secrets
interactive operations
```

Cloud-init should establish the machine.

The bring-up procedure should then qualify the machine.

---

# 10. Validate the Cloud-Init YAML Before Boot

YAML errors can prevent provisioning.

Before ejecting the SD card, inspect:

```bash
cat user-data
```

Check the YAML carefully.

The first line must be:

```yaml
#cloud-config
```

If available on the workstation, validate the cloud-config syntax using cloud-init:

```bash
cloud-init schema --config-file user-data
```

If cloud-init is not installed on the workstation, perform a careful YAML validation using an appropriate YAML parser.

Do not proceed if the configuration is malformed.

---

# 11. Safely Eject the SD Card

After editing the cloud-init files:

```bash
sync
```

Then safely unmount/eject the boot partition.

For example:

```bash
udisksctl unmount -b /dev/sdX1
```

Remove the SD card.

The provisioning sequence is now complete.

---

# 12. First Boot

Insert the SD card into the powered-off Pi.

Connect:

* Ethernet
* active cooling
* power

Do not connect the STM32 SPI interface yet.

Do not apply motor power.

Power on the Pi.

cloud-init will execute the first-boot configuration.

Canonical documents cloud-init as the first-boot mechanism responsible for initial user creation and configuration on Ubuntu Raspberry Pi images.

Allow the process to complete.

Do not interrupt power during initial provisioning.

---

# 13. Locate the Pi

Use the DHCP server/router to identify the Pi's IP address.

If mDNS is available:

```bash
ping -c 1 arm-pi-01.local
```

Then connect:

```bash
ssh robot@arm-pi-01.local
```

No password should be required.

SSH public-key authentication should be used from the first operational login.

---

# 14. Verify cloud-init

Before making further changes:

```bash
cloud-init status --wait
```

Expected:

```text
status: done
```

Then:

```bash
cloud-init status
```

Review the cloud-init log:

```bash
sudo journalctl -u cloud-init
```

and, if required:

```bash
sudo less /var/log/cloud-init.log
```

Also inspect:

```bash
sudo cloud-init analyze show
```

**If cloud-init reports an error, stop here.**

Do not manually repair the system and continue without understanding the provisioning failure.

The purpose of this workflow is reproducibility.

---

# 15. Verify the Provisioned System

Run:

```bash
hostnamectl
```

```bash
uname -a
```

```bash
cat /etc/os-release
```

```bash
ip -brief address
```

Verify:

```text
hostname = arm-pi-01
Ubuntu = 24.04 LTS
Ethernet = connected
```

Verify the user:

```bash
id robot
```

Verify SSH:

```bash
sudo sshd -T | grep -E \
'passwordauthentication|pubkeyauthentication|permitrootlogin'
```

Expected:

```text
passwordauthentication no
pubkeyauthentication yes
permitrootlogin no
```

---

# 16. Establish the Base System

The cloud-init configuration performs the initial package update.

After first boot, explicitly verify package state:

```bash
sudo apt update
```

Then:

```bash
sudo apt full-upgrade -y
```

Remove obsolete packages:

```bash
sudo apt autoremove --purge -y
```

Reboot:

```bash
sudo reboot
```

Reconnect:

```bash
ssh robot@arm-pi-01.local
```

---

# 17. Verify Time Synchronization

The Raspberry Pi is the project time authority.

Check:

```bash
timedatectl status
```

Then:

```bash
chronyc tracking
```

Do not begin STM32 time-synchronization validation until:

```text
chronyc tracking
```

shows a synchronized source.

The Pi's system clock is the reference used by the host-side system.

---

# 18. Configure Additional Maintenance Access

Only create a separate maintenance account if required.

For example:

```bash
sudo adduser maint
```

Then:

```bash
sudo usermod -aG sudo maint
```

Install the appropriate public SSH key.

If the maintenance account is required on every deployed Pi, its creation should eventually be moved into the version-controlled cloud-init configuration.

Do not run the robot control system as `root`.

---

# 19. Ubuntu PREEMPT_RT

Ubuntu's real-time kernel for Raspberry Pi requires Ubuntu Pro.

Obtain an Ubuntu Pro token separately.

**Do not place the token in `user-data` or source control.**

Attach Ubuntu Pro:

```bash
sudo pro attach
```

Then enable the Raspberry Pi real-time kernel:

```bash
sudo pro enable realtime-kernel --variant=raspi
```

Reboot:

```bash
sudo reboot
```

Verify:

```bash
uname -a
```

```bash
uname -r
```

```bash
cat /sys/kernel/realtime
```

```bash
pro status
```

The following must report:

```text
1
```

from:

```bash
cat /sys/kernel/realtime
```

If not, stop.

Inspect:

```bash
sudo journalctl -b -k
```

Do not continue assuming PREEMPT_RT is active.

Retain the standard kernel as a recovery option until the complete hardware test plan has passed.

---

# 20. Configure Real-Time Permissions

Create:

```bash
sudo groupadd --force realtime
```

Add `robot`:

```bash
sudo usermod -aG realtime robot
```

Create:

```text
/etc/security/limits.d/99-robot-realtime.conf
```

with:

```text
@realtime soft rtprio 99
@realtime hard rtprio 99

@realtime soft priority 99
@realtime hard priority 99

@realtime soft memlock unlimited
@realtime hard memlock unlimited
```

Log out completely and reconnect.

Verify:

```bash
id
```

```bash
ulimit -r
```

```bash
ulimit -l
```

Expected:

```text
99
unlimited
```

Do not give real-time scheduling privileges to general-purpose users.

---

# 21. Configure CPU Governor

Install:

```bash
sudo apt install -y linux-tools-$(uname -r) cpufrequtils
```

Set:

```bash
sudo cpupower frequency-set -g performance
```

Verify:

```bash
cpupower frequency-info | grep 'current policy'
```

Do not initially introduce:

```text
isolcpus
nohz_full
rcu_nocbs
IRQ pinning
custom kernel command-line parameters
```

First establish a measured baseline.

Premature CPU isolation or IRQ manipulation can make latency worse rather than better.

---

# 22. Install ROS 2 Jazzy

Ubuntu 24.04 corresponds to ROS 2 Jazzy.

Install prerequisites:

```bash
sudo apt update

sudo apt install -y \
  locales \
  software-properties-common \
  curl
```

Configure locale:

```bash
sudo locale-gen en_US en_US.UTF-8

sudo update-locale \
  LC_ALL=en_US.UTF-8 \
  LANG=en_US.UTF-8
```

Enable Universe:

```bash
sudo add-apt-repository universe
```

Install the ROS key:

```bash
sudo curl -sSL \
  https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
```

Add the repository:

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" |
  sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null
```

Install:

```bash
sudo apt update

sudo apt install -y \
  ros-jazzy-ros-base \
  ros-dev-tools \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-controller-manager \
  ros-jazzy-joint-state-broadcaster
```

Add ROS to the shell:

```bash
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
```

Then:

```bash
source /opt/ros/jazzy/setup.bash
```

Verify:

```bash
ros2 doctor --report
```

---

# 23. Create the ROS Workspace

Create:

```bash
mkdir -p ~/arm_sensor_hub_ws/src
```

Then:

```bash
cd ~/arm_sensor_hub_ws
```

Build:

```bash
colcon build --symlink-install
```

Add the workspace:

```bash
echo 'source ~/arm_sensor_hub_ws/install/setup.bash' >> ~/.bashrc
```

Keep all project software under version control.

Do not modify packages below:

```text
/opt/ros
```

---

# 24. Enable SPI

The STM32 is the SPI slave.

The Pi is the SPI master.

Before enabling SPI, freeze the following in the hardware harness documentation:

* SPI controller
* SCK pin
* MOSI pin
* MISO pin
* NSS/CS pin
* `DATA_READY` GPIO
* SPI mode
* maximum clock rate

Inspect the current state:

```bash
ls -l /dev/spidev* || true
```

```bash
grep -R "dtparam=spi\|dtoverlay=.*spi" \
  /boot/firmware/config.txt \
  /boot/firmware/usercfg.txt 2>/dev/null || true
```

Inspect overlays:

```bash
ls /boot/firmware/overlays | grep spi
```

For the selected primary SPI interface:

```text
dtparam=spi=on
```

Do not enable an SPI controller merely because it exists.

Confirm the physical pin mapping and intended `/dev/spidevB.C` mapping first.

Reboot:

```bash
sudo reboot
```

Verify:

```bash
ls -l /dev/spidev*
```

---

# 25. Configure GPIO

Use libgpiod for GPIO access.

Inspect:

```bash
gpioinfo
```

The host driver must request the correct line as an input with the required edge event and bias.

Do not use a GPIO number copied from an unrelated example.

Do not use deprecated sysfs GPIO interfaces.

---

# 26. Connect the STM32

Power off before connecting the SPI interface.

Verify:

* common ground
* 3.3 V-only signalling
* SCK direction
* MOSI direction
* MISO direction
* NSS direction
* `DATA_READY`
* short return path
* no back-powering
* STM32 reset state
* STM32 power state

Motor power must remain removed.

---

# 27. Initial SPI Validation

Begin at a conservative SPI clock.

The project's initial maximum is:

```text
5 MHz
```

This is not considered approved merely because the Pi and STM32 can theoretically operate at that rate.

Validate:

* DMA behaviour
* NSS behaviour
* `DATA_READY` detection
* CRC
* sequence handling
* signal integrity
* transaction timing

The host must validate:

```text
frame magic
version
length
CRC32
sequence number
```

before accepting a frame.

Initially test only:

```text
status
snapshot
time synchronisation
```

Do not send motion commands merely to prove that SPI works.

---

# 28. Configure ros2_control Safety Defaults

The controller manager must not automatically activate physical hardware at boot.

The STM32-backed hardware component should start:

```text
inactive
```

Example:

```yaml
controller_manager:
  ros__parameters:

    update_rate: 100

    enforce_command_limits: true

    hardware_components_initial_state:
      inactive:
        - arm_sensor_hub

      shutdown_on_initial_state_failure: true

    defaults:
      allow_controller_activation_with_inactive_hardware: false
      deactivate_controllers_on_hardware_self_deactivate: true
```

The initial 100 Hz rate is a starting point.

The final rate must be established from measured:

```text
sensor acquisition
+
SPI transfer
+
hardware read
+
controller update
+
EKF
+
command generation
+
hardware write
```

The STM32 remains the final safety authority.

---

# 29. Configure Real-Time Controller Behaviour

Initially target:

```text
lock_memory: true
thread_priority: 50
```

Do not introduce CPU affinity until baseline latency measurements identify a suitable CPU.

The EKF must not bypass the STM32 command-safety path.

Invalid, stale or incoherent sensor frames must become faults.

---

# 30. Create the Managed systemd Service

Do not launch robot control from an SSH shell during deployment.

Create:

```text
/etc/systemd/system/arm-sensor-hub.service
```

Example:

```ini
[Unit]
Description=Arm Sensor Hub ROS 2 bring-up
After=network-online.target chrony.service
Wants=network-online.target

[Service]
Type=simple

User=robot
Group=robot

WorkingDirectory=/home/robot/arm_sensor_hub_ws

Environment=ROS_DOMAIN_ID=0

ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && source /home/robot/arm_sensor_hub_ws/install/setup.bash && exec ros2 launch arm_sensor_hub_bringup hardware_inactive.launch.py'

Restart=on-failure
RestartSec=2

LimitRTPRIO=99
LimitMEMLOCK=infinity

NoNewPrivileges=false

[Install]
WantedBy=multi-user.target
```

Replace:

```text
arm_sensor_hub_bringup
```

and:

```text
hardware_inactive.launch.py
```

with the actual project package and launch file.

The launch file must not activate motors implicitly.

Enable:

```bash
sudo systemctl daemon-reload
```

Then:

```bash
sudo systemctl enable --now arm-sensor-hub.service
```

Verify:

```bash
sudo systemctl status arm-sensor-hub.service --no-pager
```

Operational commands:

```bash
sudo systemctl restart arm-sensor-hub.service
```

```bash
sudo journalctl -u arm-sensor-hub.service -b -f
```

```bash
sudo systemctl disable --now arm-sensor-hub.service
```

---

# 31. Measure Real-Time Behaviour

Measure the RT kernel under idle and representative load.

Initial test:

```bash
sudo cyclictest \
  --smp \
  -p95 \
  -m \
  -i200 \
  -h400 \
  -q \
  -a3 \
  -D 300s
```

In another session:

```bash
stress-ng \
  --cpu 3 \
  --io 2 \
  --vm 1 \
  --vm-bytes 512M \
  --timeout 300s \
  --metrics-brief
```

Record:

* maximum latency
* average latency
* kernel version
* governor
* CPU temperature
* active services
* test duration

Repeat with:

* ROS running
* SPI traffic
* logging
* network traffic
* representative system load

Establish an explicit latency budget from the controller period and SPI transaction deadline.

Do not judge real-time suitability from average latency.

---

# 32. Verify Controller Scheduling

Inspect:

```bash
ps -eLo pid,tid,cls,rtprio,pri,psr,comm |
  grep -E 'ros2_control|controller_manager'
```

Check memory locking:

```bash
grep -E 'VmLck|CapEff' \
  /proc/$(pgrep -o ros2_control_node)/status
```

Adapt the process lookup if the executable name differs.

Preserve the results with the deployment record.

---

# 33. Acceptance Sequence

Complete each stage in order.

A failure returns the system to the previous safe stage.

## 33.1 OS

Verify:

* SSH key login
* Ubuntu version
* package state
* network connectivity
* time synchronization
* RT kernel

## 33.2 Cloud-Init

Verify:

```bash
cloud-init status
```

reports:

```text
status: done
```

Review the cloud-init logs for provisioning failures.

## 33.3 Real-Time Permissions

Verify:

* `robot` has `realtime`
* SPI access is correct
* GPIO access is correct
* `rtprio` is correct
* memlock is unlimited

## 33.4 Thermal / Load

Verify:

* no undervoltage events
* no thermal throttling
* adequate cooling
* acceptable temperature under representative load

If available:

```bash
vcgencmd get_throttled
```

## 33.5 SPI Electrical

With motor power absent, verify using a logic analyser:

* voltage levels
* pin mapping
* clock polarity
* clock phase
* chip select
* `DATA_READY`
* transaction timing

## 33.6 SPI Protocol

Verify:

* status frames
* snapshot frames
* time-sync frames
* CRC
* sequence numbers
* stale-frame rejection
* STM32 reset recovery
* host restart recovery

## 33.7 Fault Behaviour

Test:

* SPI disconnect
* time-sync interruption
* malformed frames
* stale frames
* STM32 reset
* Pi restart

Verify that no unsafe command is accepted.

## 33.8 ROS Lifecycle

Verify:

* hardware starts inactive
* explicit activation requires healthy transport
* hardware faults are propagated
* command-owning controllers deactivate appropriately

## 33.9 Motion Release

Only after all preceding tests pass:

Follow every requirement in:

```text
SAFETY_RELEASE_CHECKLIST.md
```

before applying motor power or commanding motion.

---

# 34. Reproducible Provisioning

The target system should be reproducible from:

```text
Ubuntu Server image
        +
cloud-init configuration
        +
version-controlled ROS workspace
        +
controlled secrets
        +
hardware-specific configuration
```

The SD-card creation procedure should therefore be:

```text
1. Insert blank SD card
        ↓
2. Open Raspberry Pi Imager
        ↓
3. Select Raspberry Pi 5
        ↓
4. Select Ubuntu Server 24.04 LTS 64-bit
        ↓
5. Select SD card
        ↓
6. NO Imager customisation
        ↓
7. Write + verify
        ↓
8. Remove/reinsert SD card
        ↓
9. Mount boot partition
        ↓
10. Configure cloud-init
        ↓
11. Validate cloud-init YAML
        ↓
12. Safely eject SD card
        ↓
13. Insert into Pi
        ↓
14. Boot
        ↓
15. cloud-init provisions machine
        ↓
16. Verify cloud-init
        ↓
17. Continue system bring-up
```

This is the standardisation boundary for the project.

---

# 35. Ongoing Operations

Apply OS and ROS security updates during a maintenance window.

After kernel changes, rerun:

* RT validation
* SPI validation
* latency testing
* ROS lifecycle testing
* safety acceptance testing

Keep:

* known-good SD/SSD image
* cloud-init configuration
* recovery procedure
* console recovery method

Monitor:

```text
journalctl
clock synchronisation
free storage
temperature
undervoltage/throttling
controller-manager diagnostics
SPI diagnostics
```

Back up:

* ROS workspace
* systemd units
* hardware configuration
* calibration records
* deployment records
* cloud-init configuration

Do not commit:

* private SSH keys
* Ubuntu Pro tokens
* passwords
* other secrets

to the repository.

Treat changes to the following as controlled changes requiring fresh timing and integration evidence:

* SPI overlays
* pin assignments
* kernel parameters
* kernel version
* controller update rate
* CPU affinity
* RT priority
* cloud-init provisioning
* hardware interface configuration

---

# 36. Recommended Project Structure

Keep the provisioning configuration separate from the ROS software:

```text
arm-sensor-hub/
├── provisioning/
│   ├── raspberry-pi/
│   │   ├── cloud-init/
│   │   │   ├── meta-data
│   │   │   ├── user-data
│   │   │   └── network-config
│   │   │
│   │   ├── systemd/
│   │   │   └── arm-sensor-hub.service
│   │   │
│   │   └── README.md
│   │
│   └── deployment/
│       └── ...
│
├── ros_ws/
│   └── src/
│
├── contracts/
│   ├── SPI_CONTRACT.md
│   ├── LIFECYCLE_CONTRACT.md
│   └── ...
│
└── SAFETY_RELEASE_CHECKLIST.md
```

The cloud-init files become the **machine provisioning source of truth**.

The ROS workspace becomes the **software source of truth**.

The contracts become the **interface source of truth**.

The safety checklist becomes the **motion-release source of truth**.

---

# 37. Recommended-Practice Assessment

The resulting workflow follows recommended practices in the important areas.

| Area                                                   | Assessment                                         |
| ------------------------------------------------------ | -------------------------------------------------- |
| Raspberry Pi Imager for Ubuntu image                   | **Recommended**                                    |
| Ubuntu Server 24.04 LTS                                | **Appropriate**                                    |
| 64-bit Raspberry Pi image                              | **Recommended**                                    |
| Imager used only to write image                        | **Good practice for reproducibility**              |
| No Imager customisation                                | **Good practice when cloud-init is authoritative** |
| cloud-init for first-boot configuration                | **Officially supported**                           |
| Editing cloud-init on boot partition before first boot | **Officially documented by Canonical**             |
| SSH public-key authentication                          | **Recommended**                                    |
| Ethernet during commissioning                          | **Recommended**                                    |
| DHCP during initial commissioning                      | **Sensible default**                               |
| Secrets excluded from repository                       | **Required practice**                              |
| Ubuntu Pro token entered separately                    | **Recommended**                                    |
| PREEMPT_RT validated rather than assumed               | **Good practice**                                  |
| Real-time performance measured                         | **Required for this application**                  |
| SPI brought up before motor power                      | **Good safety practice**                           |
| Hardware initially inactive                            | **Good safety practice**                           |
| Logic-analyser validation                              | **Good engineering practice**                      |
| Explicit acceptance sequence                           | **Strong practice**                                |
| Version-controlled provisioning                        | **Strong practice**                                |
| Avoiding premature CPU isolation                       | **Good practice**                                  |

Canonical's current Ubuntu Raspberry Pi documentation specifically states that the pre-installed image's cloud-init seed is on the boot partition and that the `user-data` and `network-config` files can be customised before boot.

### One important qualification

I would **not** describe every subsequent step in this guide as an "Ubuntu recommended practice." There is an important distinction:

* **Ubuntu/Canonical-supported:** Ubuntu image, Raspberry Pi Imager, cloud-init, SSH provisioning, boot-partition seed.
* **Project engineering decisions:** PREEMPT_RT configuration, SPI configuration, ROS 2 configuration, `ros2_control` safety policy, latency requirements, CPU governor, controller scheduling and the acceptance sequence.

Those latter decisions should be justified by your system requirements and measured evidence rather than attributed to Canonical.

The **Imager → edit cloud-init → first boot** portion, however, is directly aligned with Canonical's documented Raspberry Pi workflow.
