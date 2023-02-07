--[[
This is a bare minimum S2E config file to demonstrate the use of libs2e with PyKVM.
Please refer to the S2E documentation for more details.
This file was automatically generated at {{ creation_time }}
]]--

s2e = {
    logging = {
        -- Possible values include "all", "debug", "info", "warn" and "none".
        -- See Logging.h in libs2ecore.
        console = "{{ loglevel }}",
        logLevel = "{{ loglevel }}",
    },
    -- All the cl::opt options defined in the engine can be tweaked here.
    -- This can be left empty most of the time.
    -- Most of the options can be found in S2EExecutor.cpp and Executor.cpp.
    kleeArgs = {
		"--verbose-on-symbolic-address=true",
		"--verbose-state-switching={{ klee_debug }}",
		"--verbose-fork-info={{ klee_debug }}",
		"--print-mode-switch={{ klee_debug }}",
		"--fork-on-symbolic-address=false",--no self-modifying code and load libs for IoT firmware
		"--suppress-external-warnings=true"
    },
}

--rom start should be equal to vtor
mem = {
	rom = {
		{% for ro in rom %} {{ '{' }}{{ ro }}{{ '}' }}, {% endfor %}
	},
	ram = {
		{% for ra in ram %} {{ '{' }}{{ ra }}{{ '}' }}, {% endfor %}
	},
}

init = {
   vtor = {{ vtor }},
}

-- Declare empty plugin settings. They will be populated in the rest of
-- the configuration file.
plugins = {}
pluginsConfig = {}

-- Include various convenient functions
dofile('library.lua')


add_plugin("NLPPeripheralModel")
pluginsConfig.NLPPeripheralModel= {
	NLPfileName = "{{ nlp_file_name }}",
    forkPoint = {{ fork_point }},
    nlp_mmio = {
		{% for nlp_mmio in nlp_mmio_range %} {{ '{' }}{{ nlp_mmio }}{{ '}' }}, {% endfor %}
    },
}

add_plugin("ExternalHardwareSignal")
pluginsConfig.ExternalHardwareSignal= {
	SignalfileName = "{{ signal_file_name }}",
}

add_plugin("ComplianceCheck")
pluginsConfig.ComplianceCheck= {
	CCfileName = "{{ CC_file_name }}",
}

add_plugin("ExternalInterrupt")
pluginsConfig.ExternalInterrupt ={
	disableSystickInterrupt = {{ disable_systick }},
	{% if disable_systick == "true" %}systickBeginPoint = {{ systick_begin_point }},{% endif %}
	disableIrqs = {
        {% for i in disable_irqs %}
        {{ i }},{% endfor %}
	},
}

add_plugin("InvalidStatesDetection")
pluginsConfig.InvalidStatesDetection = {
	bb_inv1 = {{ bb_inv1 }},
	bb_inv2 = {{ bb_inv2 }},
	killPoints = {
        {% for k in kill_points %}
        {{ k }},{% endfor %}
	},
	alivePoints = {
        {% for a in alive_points %}
        {{ a }},{% endfor %}
	}
}

<<<<<<< HEAD



=======
>>>>>>> bb37982f944d2541865f552fc1650e6e869e9be2
add_plugin("SymbolicHardware")
add_plugin("FailureAnalysis")


