# Karetao Project Questions Register

This file is the canonical register of project questions that must be answered before the corresponding requirements, interfaces, implementation decisions, or release gates can be considered complete.

Questions are grouped by topic. Answers should be recorded against the question, with a reference to the decision, requirement, test result, or other authoritative document where appropriate.

## 1. System Scope and Architecture

1. What is the complete end-to-end Karetao system architecture, including the STM32, Raspberry Pi, ROS 2, MoveIt 2, ros2_control, and optional EKF?
2. Which components are mandatory for the first operational release, and which are optional or deferred?
3. What constitutes a fully functioning Karetao system?
4. What exact conditions must be satisfied before motion is permitted?
5. Which subsystem has final authority to permit or inhibit motion?
6. How are subsystem health states exposed and evaluated?
7. What happens if any required subsystem becomes unavailable during operation?
8. What is the required system startup, initialization, and shutdown sequence?
9. What is the required recovery sequence after a system fault?
10. Which interfaces between the major Karetao sub-repositories are authoritative?

## 2. User Interface and Command Model

11. How does the user specify the desired end-effector position?
12. Does the user provide XYZ position only, or a complete 3D pose including orientation?
13. If orientation is specified, what representation is used?
14. What coordinate frame is used for user commands?
15. What coordinate frames are required throughout the system?
16. How are invalid, unreachable, or unsafe target poses handled?
17. What feedback does the user receive when a command is accepted, rejected, or interrupted?
18. Can the user command individual joints directly, or only end-effector poses?
19. What command rate and update behaviour are required?

## 3. Mechanical Configuration and Degrees of Freedom

20. What are the exact mechanical joint definitions and names?
21. Are there exactly six controllable mechanical degrees of freedom?
22. What are the limits, zero positions, and positive directions of each joint?
23. Which joints contain gearboxes?
24. How are joints 1–4 mechanically related to the X, Y, Z, and wrist axes?
25. How exactly does the two-motor differential end effector map motor motion to its two rotational degrees of freedom?
26. What are the mathematical forward and inverse mappings for the differential mechanism?
27. What are the mechanical limits and safe operating limits of the differential end effector?
28. Are there mechanical couplings, backlash, compliance, or other effects that must be represented in the control model?
29. What is the authoritative joint naming and ordering convention?

## 4. Sensors and Sensor Data

30. Which sensors are installed on the STM32 sensor hub?
31. What physical quantity does each sensor measure?
32. What are the range, resolution, accuracy, noise characteristics, and expected update rate of each sensor?
33. What sensor acquisition rate is required for normal operation?
34. Is 500 Hz a hard requirement or a target for EKF sampling?
35. Which sensors are sampled synchronously?
36. What constitutes a valid sensor sample?
37. How are missing, stale, invalid, or out-of-range sensor values detected?
38. What maximum sensor-data age is acceptable before motion must be inhibited?
39. What timestamp source is authoritative?
40. What timestamp synchronization accuracy is required between the STM32 and Raspberry Pi?
41. How is sensor calibration performed?
42. What calibration data must be retained, and where is it stored?
43. What happens when calibration is missing, invalid, or outside permitted limits?

## 5. STM32 ↔ Raspberry Pi Integration

44. What is the authoritative STM32-to-Raspberry-Pi transport and protocol?
45. What is the complete message structure in each direction?
46. What commands can the Raspberry Pi send to the STM32?
47. What sensor and health information does the STM32 send to the Raspberry Pi?
48. How are commands acknowledged?
49. What constitutes a valid command acknowledgement?
50. What acknowledgement timeout is permitted?
51. What happens when a command is not acknowledged?
52. What happens when acknowledgements are delayed, duplicated, or inconsistent?
53. How are communication failures detected?
54. What communication failure response is required?
55. What data integrity, sequencing, and freshness checks are required?
56. What is the required maximum communication latency and jitter?
57. How is the interface versioned and kept compatible across the two systems?

## 6. Motor Control and ros2_control

58. What is the authoritative motor command interface?
59. Which subsystem converts ROS joint commands into STM32 motor commands?
60. How are motor commands mapped to physical joints?
61. How are gearbox ratios represented?
62. How is the differential end-effector mapping represented in ros2_control?
63. What command, state, and feedback interfaces are required by ros2_control?
64. How is motor-command acknowledgement exposed to ros2_control?
65. What happens if the STM32 does not acknowledge a motor command?
66. What happens if motor feedback disagrees with the commanded state?
67. What command timeout or watchdog behaviour is required?
68. What is the required motor-control update rate?
69. How are joint limits enforced?
70. How are velocity, acceleration, and other motion limits enforced?

## 7. MoveIt 2 and Motion Planning

71. What MoveIt 2 planning model is required?
72. What robot description format and source are authoritative?
73. How are joint limits supplied to MoveIt 2?
74. What collision model is required?
75. What self-collision and environment-collision constraints are required?
76. How are unreachable or collision-producing trajectories handled?
77. What planner configuration is required for the first release?
78. How is a planned trajectory validated before execution?
79. What happens if the system becomes unhealthy while a trajectory is executing?
80. How is trajectory execution cancelled or stopped after a fault?

## 8. EKF and State Estimation

81. Is an EKF required for the first operational release?
82. If used, which sensor measurements are fused?
83. What state variables does the EKF estimate?
84. What is the required EKF update rate?
85. Is 500 Hz required for the EKF, and can the complete sensor/communication/control chain sustain it?
86. What maximum input-data age and latency can the EKF tolerate?
87. How are missing or invalid measurements handled?
88. How is EKF health determined?
89. What happens to motion if the EKF becomes unhealthy?
90. Which estimated states are exposed to ros2_control or MoveIt 2?

## 9. Safety and Fault Handling

91. What exact faults must cause immediate motion inhibition?
92. Does any sensor-data failure require an immediate stop, or are there defined tolerances for transient failures?
93. Does any unacknowledged motor command require an immediate stop?
94. What does “stop immediately” mean in measurable system terms?
95. What is the maximum permitted fault-to-motion-stop latency?
96. Which subsystem owns the emergency-stop function?
97. Is there a separate physical E-stop, and how is it integrated?
98. What is the safe state of each motor and actuator after a fault?
99. Can motion resume automatically after recovery, or must an explicit reset be performed?
100. What conditions are required before motion can resume?
101. How are faults latched, reported, logged, and cleared?
102. What safety standards or engineering practices must the project comply with?
103. What safety validation and acceptance tests are required before physical motion?

## 10. Calibration, Configuration, and Startup

104. What configuration values are required before the system can operate?
105. Which values are fixed hardware parameters and which are runtime configuration?
106. Where are calibration and configuration values stored?
107. How are configuration versions managed?
108. What startup self-tests are required?
109. What must be verified before enabling motor power?
110. What conditions prevent startup from progressing to an armed state?
111. How are configuration or calibration mismatches detected?
112. What is the required procedure for commissioning a new or modified arm?

## 11. Testing and Acceptance

113. What is the required hardware-integration test sequence?
114. What is the minimum test required to prove valid STM32 sensor data?
115. What is the minimum test required to prove valid motor commands?
116. What proves that STM32 command acknowledgements are reliable?
117. What proves that sensor-data failure inhibits motion?
118. What proves that missing motor acknowledgement inhibits motion?
119. What proves that the system cannot execute motion until all required systems are healthy?
120. What proves that motion stops within the required fault-response time?
121. What tests validate the differential end-effector mapping?
122. What tests validate joint limits and trajectory limits?
123. What tests validate MoveIt 2 planning and collision avoidance?
124. What tests validate EKF performance, if the EKF is enabled?
125. What are the acceptance criteria for the first physical motion test?
126. What are the acceptance criteria for the first complete end-to-end pose command?

## 12. Requirements and Documentation

127. Which document is authoritative for system requirements?
128. Which document is authoritative for system-level decisions?
129. Which documents are contractual interfaces versus implementation notes?
130. How are unresolved questions tracked through to decisions?
131. How are requirements traced to implementation and verification evidence?
132. What information currently marked as unspecified must be defined in the next revision?
133. What is the process for approving changes to frozen contracts?
134. How are obsolete documents identified and archived?
135. How is the project documentation kept synchronized across Karetao sub-repositories?

## 13. Project Planning and Release

136. What is the exact scope of the first release?
137. What functionality is explicitly deferred?
138. What dependencies must be completed before ROS 2 development begins?
139. What is the exit criterion for STM32 ↔ Raspberry Pi hardware integration?
140. What is the exit criterion for beginning MoveIt 2 and ros2_control integration?
141. What is the exit criterion for enabling physical motion?
142. Which requirements are hard constraints versus engineering targets?
143. Which remaining values and parameters must be specified in the next project revision?
144. Who is responsible for answering and approving each unresolved question?
145. What evidence is required before each answer is considered closed?
