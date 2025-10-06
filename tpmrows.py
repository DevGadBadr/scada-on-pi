tpm_registers = [
    # enabled, address, parameter, datatype, readwrite, multiplier, unit
    (True, 4000, "L1 Voltage", "uint16", "R", 0.1, "V"),
    (True, 4001, "L2 Voltage", "uint16", "R", 0.1, "V"),
    (True, 4002, "L3 Voltage", "uint16", "R", 0.1, "V"),

    (True, 4024, "L1 Current", "uint16", "R", 0.001, "A"),
    (True, 4025, "L2 Current", "uint16", "R", 0.001, "A"),
    (True, 4026, "L3 Current", "uint16", "R", 0.001, "A"),
    (True, 4027, "Neutral Current", "uint16", "R", 0.001, "A"),

    (True, 4040, "L1 Frequency", "uint16", "R", 0.01, "Hz"),
    (True, 4041, "L2 Frequency", "uint16", "R", 0.01, "Hz"),
    (True, 4042, "L3 Frequency", "uint16", "R", 0.01, "Hz"),

    (True, 4043, "L1 Power Factor", "int16", "R", 0.001, ""),
    (True, 4044, "L2 Power Factor", "int16", "R", 0.001, ""),
    (True, 4045, "L3 Power Factor", "int16", "R", 0.001, ""),
    (True, 4046, "Total Power Factor", "int16", "R", 0.001, ""),

    (True, 4140, "L1 Active Power", "int32", "R", 0.001, "W"),
    (True, 4142, "L2 Active Power", "int32", "R", 0.001, "W"),
    (True, 4144, "L3 Active Power", "int32", "R", 0.001, "W"),
    (True, 4146, "Total Active Power", "int32", "R", 0.001, "W"),

    (True, 4162, "L1 Reactive Power", "int32", "R", 0.001, "Var"),
    (True, 4164, "L2 Reactive Power", "int32", "R", 0.001, "Var"),
    (True, 4166, "L3 Reactive Power", "int32", "R", 0.001, "Var"),
    (True, 4168, "Total Reactive Power", "int32", "R", 0.001, "Var"),

    (True, 4184, "L1 Apparent Power", "uint32", "R", 0.001, "VA"),
    (True, 4186, "L2 Apparent Power", "uint32", "R", 0.001, "VA"),
    (True, 4188, "L3 Apparent Power", "uint32", "R", 0.001, "VA"),
    (True, 4190, "Total Apparent Power", "uint32", "R", 0.001, "VA"),

    (True, 4222, "Total Active Import Energy", "uint64", "R", 1, "Wh"),
    (True, 4238, "Total Active Export Energy", "uint64", "R", 1, "Wh"),
    (True, 4254, "Total Inductive Energy", "uint64", "R", 1, "Varh"),
    (True, 4270, "Total Capacitive Energy", "uint64", "R", 1, "Varh"),
    (True, 4292, "Total Apparent Energy", "uint64", "R", 1, "VAh"),
]
