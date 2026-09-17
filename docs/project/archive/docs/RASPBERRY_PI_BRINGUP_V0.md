# Raspberry Pi 5 Bring-Up Guide

This procedure provisions a Raspberry Pi 5 (8 GB) as the Ubuntu Server, PREEMPT_RT, ROS 2, and STM32 host for Arm Sensor Hub. It assumes Ubuntu Server 24.04 LTS arm64, Ethernet during commissioning, and all post-imaging work performed over SSH.

The Pi is the SPI master and system-time authority. The STM32 remains responsible for sensor acquisition, CAN transport, low-level lifecycle enforcement, and safe command rejection. Do not energize motors until the hardware and acceptance sections are complete.

See [SPI Host Contract](SPI_CONTRACT.md), [Lifecycle Contract](LIFECYCLE_CONTRACT.md), and [Safety Release Checklist](SAFETY_RELEASE_CHECKLIST.md) before connecting an energized system.

## 1. Prepare Hardware

Obtain:

- Raspberry Pi 5, 8 GB RAM, official 27 W USB-C power supply, and active cooler.
- A reliable 32 GB or larger high-endurance microSD card for commissioning. Use an SSD or other robust boot media for a deployed robot.
- Wired Ethernet and a DHCP-enabled network.
- A dedicated, non-shared 3.3 V SPI connection between Pi and STM32, with a common ground.
- A separate emergency-stop/power-interlock path. Neither Linux nor the SPI link is an emergency stop.

Before first boot, update the Pi bootloader EEPROM if the board has been stored for a long time. Follow the Raspberry Pi Foundation EEPROM update procedure using Raspberry Pi Imager or a temporary Raspberry Pi OS boot card. Do not interrupt power during an EEPROM update.

## 2. Create the Ubuntu Server SD Card

Perform these steps on the workstation that has the SD card reader.

1. Install and open Raspberry Pi Imager. On Ubuntu:

   ```bash
   sudo snap install rpi-imager
   rpi-imager
   ```

2. Select **Raspberry Pi 5**, then select **Ubuntu Server 24.04 LTS (64-bit)**. Do not select Desktop or Ubuntu Core.
3. Select the intended SD card. Verify the selected device carefully: writing the image erases that device.
4. In the Imager customization dialog, configure:
   - Hostname: `arm-pi-01` (or your site-specific, DNS-safe hostname).
   - Username: `robot`. 
   - A unique password. Store it in the team password manager, not in this repository.
   - SSH: enable it and import the workstation public key. Prefer key-only SSH from first boot.
   - Locale/time zone/keyboard appropriate to the deployment site.
   - Wi-Fi only when Ethernet is impossible. Prefer Ethernet for commissioning and deployed control.
5. Write the image, let Imager verify it, eject the card cleanly, insert it in the Pi, attach Ethernet, cooling, and power.

Record the hostname, MAC address, SD-card model, and physical Pi serial number in the deployment record.

## 3. First Boot and SSH Access

Wait for the first boot to complete; cloud-init may take several minutes. Find the IP from the DHCP server, your router, or mDNS:

```bash
ping -c 1 arm-pi-01.local
ssh robot@arm-pi-01.local
```

Confirm the machine and OS before changing it:

```bash
hostnamectl
uname -a
cat /etc/os-release
ip -brief address
```

If SSH does not come up, use a local HDMI/keyboard or a 3.3 V USB-to-UART adapter on the Pi debug UART. Do not connect a 5 V UART adapter.

## 4. Update and Establish the Base System

All remaining commands run over SSH as `robot`, unless stated otherwise.

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt autoremove --purge -y
sudo reboot
```

Reconnect and install baseline administration, diagnostics, build, and latency-test tools:

```bash
ssh robot@arm-pi-01.local
sudo apt update
sudo apt install -y \
  build-essential cmake ninja-build git pkg-config \
  curl ca-certificates gnupg lsb-release software-properties-common \
  chrony ethtool htop i2c-tools spi-tools gpiod \
  stress-ng rt-tests linux-tools-common
```

Set a stable timezone and verify that time is synchronized. Replace the example time zone if required.

```bash
sudo timedatectl set-timezone Europe/London
timedatectl status
chronyc tracking
```

The Pi time is the project time authority. Do not begin STM32 time-sync validation until `chronyc tracking` reports a synchronized source.

## 5. Create Users and Least-Privilege Access

Keep `robot` as the deployment/control account. Create a separate non-real-time maintenance account only if required:

```bash
sudo adduser maint
sudo usermod -aG sudo maint
```

Grant only the peripheral groups needed by the host process. Group names are distribution and device-node dependent, so check them after SPI is enabled:

```bash
getent group spi
getent group gpio
sudo usermod -aG spi,gpio robot
id robot
```

The new group membership takes effect only after logging out and back in. Do not run the control service as `root` to work around permissions.

Install the operations team public keys for each authorized account:

```bash
install -d -m 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Before disabling password authentication, open a second SSH session and verify that public-key login works. Then create `/etc/ssh/sshd_config.d/10-arm-sensor-hub.conf`:

```bash
sudo tee /etc/ssh/sshd_config.d/10-arm-sensor-hub.conf >/dev/null <<'EOF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AllowUsers robot maint
EOF
sudo sshd -t
sudo systemctl reload ssh
```

Remove `maint` from `AllowUsers` if it is not created. Test a new key-only SSH connection before closing the existing session.

Limit SSH network exposure. For a trusted LAN, permit SSH only from the management subnet, replacing the example CIDR:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp
sudo ufw enable
sudo ufw status verbose
```

Do not enable a firewall rule that removes the current SSH path until a console recovery route is available.

## 6. Install Ubuntu PREEMPT_RT for Raspberry Pi

Ubuntu 24.04 Real-time Ubuntu for Pi requires Ubuntu Pro. It is free for personal and small-scale use within the applicable machine limit.

1. Obtain an Ubuntu Pro token from Canonical and attach it. Enter the token directly into the SSH terminal; never place it in source control, shell history exports, or this guide.

   ```bash
   sudo pro attach
   sudo pro enable realtime-kernel --variant=raspi
   sudo reboot
   ```

2. Verify that the system booted the real-time kernel:

   ```bash
   uname -a
   uname -r
   cat /sys/kernel/realtime
   pro status
   ```

   `cat /sys/kernel/realtime` must output `1`. If it does not, stop here, inspect `sudo journalctl -b -k`, confirm the kernel package is installed, and select the RT boot entry if necessary. Do not continue assuming PREEMPT_RT is active.

3. Retain the standard kernel as a recovery boot option until the system has passed its full hardware test plan. Keep physical or serial-console recovery access available during RT-kernel changes.

## 7. Configure Real-Time Permissions

`ros2_control` attempts to run its main control loop with `SCHED_FIFO`, normally at priority 50. Permit that for the dedicated control account and allow locked memory:

```bash
sudo groupadd --force realtime
sudo usermod -aG realtime robot
sudo tee /etc/security/limits.d/99-robot-realtime.conf >/dev/null <<'EOF'
@realtime soft rtprio 99
@realtime hard rtprio 99
@realtime soft priority 99
@realtime hard priority 99
@realtime soft memlock unlimited
@realtime hard memlock unlimited
EOF
```

Log out completely, reconnect, and verify:

```bash
id
ulimit -r
ulimit -l
```

The target values are a real-time priority limit of `99` and unlimited memory locking. Do not give real-time scheduling privilege to general-purpose users or services.

Set the CPU governor to `performance` during control and latency characterization:

```bash
sudo apt install -y linux-tools-$(uname -r) cpufrequtils
sudo cpupower frequency-set -g performance
cpupower frequency-info | grep 'current policy'
```

Persist this only after confirming the command works on the selected kernel and measuring temperatures under load. The active cooler is mandatory for sustained Pi 5 control workloads.

Do not add `isolcpus`, `nohz_full`, `rcu_nocbs`, IRQ pinning, or custom kernel command-line parameters at initial bring-up. First establish a measured baseline; premature CPU isolation can move interrupts onto the wrong core and worsen latency.

## 8. Install ROS 2 Jazzy and ros2_control

Ubuntu 24.04 corresponds to ROS 2 Jazzy. Configure the ROS apt repository and install a minimal control-capable environment:

```bash
sudo apt update
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update
sudo apt install -y curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null
sudo apt update
sudo apt install -y \
  ros-jazzy-ros-base ros-dev-tools \
  ros-jazzy-ros2-control ros-jazzy-ros2-controllers \
  ros-jazzy-controller-manager ros-jazzy-joint-state-broadcaster
```

Make ROS available in interactive shells:

```bash
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
source /opt/ros/jazzy/setup.bash
ros2 doctor --report
```

For a custom hardware interface or estimator, create a colcon workspace owned by `robot`:

```bash
mkdir -p ~/arm_sensor_hub_ws/src
cd ~/arm_sensor_hub_ws
colcon build --symlink-install
echo 'source ~/arm_sensor_hub_ws/install/setup.bash' >> ~/.bashrc
```

Keep custom code, launch files, URDF, controller configuration, and systemd unit files under version control. Do not modify packages beneath `/opt/ros`.

## 9. Enable and Validate SPI and GPIO

The STM32 is the SPI3 slave and the Pi is the master. The exact Pi pins/chip-select must be frozen in the hardware harness drawing before enabling an overlay.

1. With the STM32 disconnected, identify the Pi SPI controller and available overlays:

   ```bash
   ls -l /dev/spidev* || true
   grep -R "dtparam=spi\|dtoverlay=.*spi" /boot/firmware/config.txt /boot/firmware/usercfg.txt 2>/dev/null || true
   ls /boot/firmware/overlays | grep spi
   ```

2. Enable the selected controller in `/boot/firmware/config.txt`. For the usual primary SPI interface, add the following once:

   ```text
   dtparam=spi=on
   ```

   Do not enable a controller or chip select solely because it is available. Confirm the physical pins, device-tree overlay, and intended `/dev/spidevB.C` mapping first.

3. Reboot and confirm the device node and ownership:

   ```bash
   sudo reboot
   ls -l /dev/spidev*
   groups
   ```

4. For the STM32 `DATA_READY` line, use libgpiod character-device access rather than deprecated sysfs GPIO. Identify the GPIO line from the wiring record:

   ```bash
   gpioinfo
   ```

   The custom host driver should request the line as an input with the required edge event and bias, then deassert/release it cleanly on shutdown. Do not use a random GPIO number copied from an example.

5. Wire only after power is off. Verify: common ground, 3.3 V-only signaling, correct SCK/MOSI/MISO/NSS direction, short return path, no back-powering through signal pins, and the STM32 reset/power state required by the interface contract.

6. Begin at a conservative SPI clock. The project’s initial maximum is 5 MHz, but it is not approved until hardware evidence validates DMA/NSS behavior, `DATA_READY` detectability, CRC/sequence handling, and signal integrity. The host must validate frame magic, version, length, CRC32, and sequence number before accepting data.

Never send a motion command merely to prove SPI communication. Start with status, time-sync, and snapshot requests while motor power remains removed.

## 10. Configure ros2_control Safety Defaults

The control manager should not automatically activate physical hardware on boot. Configure the STM32-backed hardware component initially as `inactive`, then activate it only after transport health, time synchronization, and the safety interlock are proven.

Example controller-manager policy:

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

Set the update rate only after measuring the complete hardware read-update-write cycle. A 100 Hz starting point is conservative; do not select a rate based on CPU capability alone. The STM32’s lifecycle and command checks remain mandatory even when `ros2_control` enforces limits.

For the controller-manager launch parameters, set `lock_memory: true`, `thread_priority: 50`, and `cpu_affinity` only after a baseline latency test identifies a suitable core. Any custom EKF must run outside the STM32 command safety path and treat invalid/stale sensor frames as faults.

## 11. Install a Managed Service

Do not launch robot control from an SSH shell in deployment. Create a dedicated `systemd` unit once the ROS bring-up package exists. This template intentionally starts the application with hardware inactive; the package launch file must not activate motors implicitly.

```text
sudo tee /etc/systemd/system/arm-sensor-hub.service >/dev/null <<'EOF'
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
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now arm-sensor-hub.service
sudo systemctl status arm-sensor-hub.service --no-pager
```

Replace `arm_sensor_hub_bringup` and `hardware_inactive.launch.py` with the actual package and launch file before enabling the service. `NoNewPrivileges=false` is required so the process can use the granted real-time scheduling privileges; compensate by running as the unprivileged `robot` user and keeping package dependencies controlled.

Use these operational commands:

```bash
sudo systemctl restart arm-sensor-hub.service
sudo journalctl -u arm-sensor-hub.service -b -f
sudo systemctl disable --now arm-sensor-hub.service
```

## 12. Measure Real-Time Behavior Before Motion

Measure idle and loaded latency with the RT kernel active. Start with a bounded test on a known CPU; the example uses CPU 3:

```bash
sudo cyclictest --smp -p95 -m -i200 -h400 -q -a3 -D 300s
```

In a separate SSH session, apply representative non-control load:

```bash
stress-ng --cpu 3 --io 2 --vm 1 --vm-bytes 512M --timeout 300s --metrics-brief
```

Record the maximum latency, average latency, kernel version, governor, CPU temperature, service set, and test duration. Repeat while the ROS application, SPI traffic, logging, and network traffic run. Establish an explicit latency budget based on the controller update period and SPI transaction deadline; do not infer acceptability from average latency.

Also confirm the actual controller-manager scheduling and memory-lock state while it runs:

```bash
ps -eLo pid,tid,cls,rtprio,pri,psr,comm | grep -E 'ros2_control|controller_manager'
grep -E 'VmLck|CapEff' /proc/$(pgrep -o ros2_control_node)/status
```

Adapt the process-name lookup if the executable differs. Preserve the evidence with the deployment record.

## 13. Acceptance Sequence

Complete each stage in order, recording results. A failure returns the system to the previous safe stage.

1. **OS:** SSH key login works; updates are current; time synchronization is healthy; RT kernel reports `1`.
2. **Real-time permissions:** `robot` has the `realtime`, `spi`, and `gpio` groups; real-time and memlock limits are effective.
3. **Thermal/load:** no undervoltage or thermal-throttling events occur under representative load. Check `vcgencmd get_throttled` if `vcgencmd` is installed.
4. **SPI electrical:** logic level, pin mapping, clock polarity/phase, chip select, and `DATA_READY` edge are verified with a logic analyzer while motor power is absent.
5. **SPI protocol:** status/snapshot/time-sync frames pass CRC, sequence, and stale-frame tests; host restarts and STM32 resets recover according to the lifecycle contract.
6. **Fault behavior:** disconnect SPI, interrupt time synchronization, inject malformed frames, and confirm no unsafe command is accepted and diagnostics become visible.
7. **ROS lifecycle:** hardware starts inactive; explicit activation works only with healthy transport; hardware errors deactivate command-owning controllers.
8. **Motion release:** satisfy every required item in [Safety Release Checklist](SAFETY_RELEASE_CHECKLIST.md) before applying motor power or commanding motion.

## 14. Ongoing Operations

- Apply OS and ROS security updates in a maintenance window and rerun the RT/SPI acceptance tests after kernel changes.
- Keep a known-good SD/SSD image and tested recovery path.
- Monitor `journalctl`, clock synchronization, free storage, temperature, undervoltage/throttling, and controller-manager diagnostics.
- Back up the ROS workspace, systemd unit, hardware configuration, SSH keys, and calibration/deployment records. Do not back up secrets into the repository.
- Treat changes to SPI overlays, pin assignments, kernel parameters, controller update rate, CPU affinity, and RT priority as controlled changes requiring fresh timing evidence.