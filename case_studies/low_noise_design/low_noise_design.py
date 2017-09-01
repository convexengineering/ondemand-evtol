#Redesign configs for low noise

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../..'))

import numpy as np
from gpkit import Model, ureg
from matplotlib import pyplot as plt
from aircraft_models import OnDemandAircraft 
from aircraft_models import OnDemandSizingMission, OnDemandRevenueMission
from aircraft_models import OnDemandDeadheadMission, OnDemandMissionCost
from study_input_data import generic_data, configuration_data
from copy import deepcopy
from collections import OrderedDict
from noise_models import vortex_noise


#General data
eta_cruise = generic_data["\eta_{cruise}"] 
eta_electric = generic_data["\eta_{electric}"]
weight_fraction = generic_data["weight_fraction"]
C_m = generic_data["C_m"]
n = generic_data["n"]

reserve_type = generic_data["reserve_type"]
autonomousEnabled = generic_data["autonomousEnabled"]
charger_power = generic_data["charger_power"]

vehicle_cost_per_weight = generic_data["vehicle_cost_per_weight"]
battery_cost_per_C = generic_data["battery_cost_per_C"]
pilot_wrap_rate = generic_data["pilot_wrap_rate"]
mechanic_wrap_rate = generic_data["mechanic_wrap_rate"]
MMH_FH = generic_data["MMH_FH"]
deadhead_ratio = generic_data["deadhead_ratio"]

delta_S = generic_data["delta_S"]

sizing_mission_type = generic_data["sizing_mission"]["type"]
sizing_N_passengers = generic_data["sizing_mission"]["N_passengers"]
sizing_mission_range = generic_data["sizing_mission"]["range"]
sizing_t_hover = generic_data["sizing_mission"]["t_{hover}"]

revenue_mission_type = generic_data["revenue_mission"]["type"]
revenue_N_passengers = generic_data["revenue_mission"]["N_passengers"]
revenue_mission_range = generic_data["revenue_mission"]["range"]
revenue_t_hover = generic_data["revenue_mission"]["t_{hover}"]

deadhead_mission_type = generic_data["deadhead_mission"]["type"]
deadhead_N_passengers = generic_data["deadhead_mission"]["N_passengers"]
deadhead_mission_range = generic_data["deadhead_mission"]["range"]
deadhead_t_hover = generic_data["deadhead_mission"]["t_{hover}"]


# Data specific to study
configs = OrderedDict()
case_array = ["Baseline","Progressive","Aggressive"]

for config in configuration_data:
	configs[config] = OrderedDict()
	for case in case_array:
		
		configs[config][case] = configuration_data[config].copy()

		if config == "Lift + cruise":
			if case == "Baseline":
				configs[config][case]["B"] = generic_data["B"]
				configs[config][case]["s"] = 0.1
				configs[config][case]["t_c"] = 0.12
			if case == "Progressive":
				configs[config][case]["B"] = 7
				configs[config][case]["s"] = 0.1
				configs[config][case]["t_c"] = 0.1
			if case == "Aggressive":
				configs[config][case]["N"] = 12
				configs[config][case]["B"] = 7
				configs[config][case]["s"] = 0.14
				configs[config][case]["t_c"] = 0.1
				configs[config][case]["Cl_{mean_{max}}"] = 1.2

		if config == "Compound heli":
			if case == "Baseline":
				configs[config][case]["B"] = generic_data["B"]
				configs[config][case]["s"] = 0.1
				configs[config][case]["t_c"] = 0.12
			if case == "Progressive":
				configs[config][case]["B"] = 3
				configs[config][case]["s"] = 0.1
				configs[config][case]["t_c"] = 0.15
			if case == "Aggressive":
				configs[config][case]["N"] = 1
				configs[config][case]["B"] = 3
				configs[config][case]["s"] = 0.1
				configs[config][case]["t_c"] = 0.15
				configs[config][case]["Cl_{mean_{max}}"] = 1.0

		if config == "Tilt wing":
			if case == "Baseline":
				configs[config][case]["B"] = generic_data["B"]
				configs[config][case]["s"] = 0.1
				configs[config][case]["t_c"] = 0.12
			if case == "Progressive":
				configs[config][case]["B"] = 7
				configs[config][case]["s"] = 0.1
				configs[config][case]["t_c"] = 0.1
			if case == "Aggressive":
				configs[config][case]["B"] = 7
				configs[config][case]["s"] = 0.14
				configs[config][case]["t_c"] = 0.1
				configs[config][case]["Cl_{mean_{max}}"] = 1.2

		if config == "Tilt rotor":
			if case == "Baseline":
				configs[config][case]["B"] = generic_data["B"]
				configs[config][case]["s"] = 0.1
				configs[config][case]["t_c"] = 0.12
			if case == "Progressive":
				configs[config][case]["B"] = 7
				configs[config][case]["s"] = 0.1
				configs[config][case]["t_c"] = 0.1
			if case == "Aggressive":
				configs[config][case]["N"] = 16
				configs[config][case]["B"] = 7
				configs[config][case]["s"] = 0.14
				configs[config][case]["t_c"] = 0.1
				configs[config][case]["Cl_{mean_{max}}"] = 1.2


#Delete unwanted configurations
del configs["Multirotor"]["Baseline"]
del configs["Multirotor"]["Progressive"]
del configs["Multirotor"]["Aggressive"]

del configs["Autogyro"]["Baseline"]
del configs["Autogyro"]["Progressive"]
del configs["Autogyro"]["Aggressive"]

del configs["Helicopter"]["Baseline"]
del configs["Helicopter"]["Progressive"]
del configs["Helicopter"]["Aggressive"]

del configs["Tilt duct"]["Baseline"]
del configs["Tilt duct"]["Progressive"]
del configs["Tilt duct"]["Aggressive"]

del configs["Coaxial heli"]["Baseline"]
del configs["Coaxial heli"]["Progressive"]
del configs["Coaxial heli"]["Aggressive"]


#Delete configurations that will not be evaluated
pared_configs = deepcopy(configs)
for config in configs:
	if configs[config] == {}:
		del pared_configs[config]
configs = deepcopy(pared_configs)

#Optimize remaining configurations
for config in configs:
	
	print "Solving configuration: " + config

	for i, case in enumerate(configs[config]):
		
		c = configs[config][case]

		V_cruise = c["V_{cruise}"]
		L_D_cruise = c["L/D"]
		T_A = c["T/A"]
		loiter_type = c["loiter_type"]
		tailRotor_power_fraction_hover = c["tailRotor_power_fraction_hover"]
		tailRotor_power_fraction_levelFlight = c["tailRotor_power_fraction_levelFlight"]

		N = c["N"]
		B = c["B"]
		s = c["s"]
		t_c = c["t_c"]
		Cl_mean_max = c["Cl_{mean_{max}}"]

		Aircraft = OnDemandAircraft(N=N,L_D_cruise=L_D_cruise,eta_cruise=eta_cruise,C_m=C_m,
			Cl_mean_max=Cl_mean_max,weight_fraction=weight_fraction,s=s,n=n,eta_electric=eta_electric,
			cost_per_weight=vehicle_cost_per_weight,cost_per_C=battery_cost_per_C,
			autonomousEnabled=autonomousEnabled)

		SizingMission = OnDemandSizingMission(Aircraft,mission_range=sizing_mission_range,
			V_cruise=V_cruise,N_passengers=sizing_N_passengers,t_hover=sizing_t_hover,
			reserve_type=reserve_type,mission_type=sizing_mission_type,loiter_type=loiter_type,
			tailRotor_power_fraction_hover=tailRotor_power_fraction_hover,
			tailRotor_power_fraction_levelFlight=tailRotor_power_fraction_levelFlight)
		SizingMission.substitutions.update({SizingMission.fs0.topvar("T/A"):T_A})
	
		RevenueMission = OnDemandRevenueMission(Aircraft,mission_range=revenue_mission_range,
			V_cruise=V_cruise,N_passengers=revenue_N_passengers,t_hover=revenue_t_hover,
			charger_power=charger_power,mission_type=revenue_mission_type,
			tailRotor_power_fraction_hover=tailRotor_power_fraction_hover,
			tailRotor_power_fraction_levelFlight=tailRotor_power_fraction_levelFlight)

		DeadheadMission = OnDemandDeadheadMission(Aircraft,mission_range=deadhead_mission_range,
			V_cruise=V_cruise,N_passengers=deadhead_N_passengers,t_hover=deadhead_t_hover,
			charger_power=charger_power,mission_type=deadhead_mission_type,
			tailRotor_power_fraction_hover=tailRotor_power_fraction_hover,
			tailRotor_power_fraction_levelFlight=tailRotor_power_fraction_levelFlight)

		MissionCost = OnDemandMissionCost(Aircraft,RevenueMission,DeadheadMission,
			pilot_wrap_rate=pilot_wrap_rate,mechanic_wrap_rate=mechanic_wrap_rate,MMH_FH=MMH_FH,
			deadhead_ratio=deadhead_ratio)
	
		problem = Model(MissionCost["cost_per_trip"],
			[Aircraft, SizingMission, RevenueMission, DeadheadMission, MissionCost])
	
		solution = problem.solve(verbosity=0)

		configs[config][case]["solution"] = solution

		configs[config][case]["MTOW"] = solution("MTOW_OnDemandAircraft")
		configs[config][case]["W_{battery}"] = solution("W_OnDemandAircraft/Battery")
		configs[config][case]["cost_per_trip_per_passenger"] = solution("cost_per_trip_per_passenger_OnDemandMissionCost")

		#Noise computations (sizing mission)
		T_perRotor = solution("T_perRotor_OnDemandSizingMission")[0]
		Q_perRotor = solution("Q_perRotor_OnDemandSizingMission")[0]
		R = solution("R")
		VT = solution("VT_OnDemandSizingMission")[0]
		s = solution("s")
		Cl_mean = solution("Cl_{mean_{max}}")
		N = solution("N")

		#Unweighted
		f_peak, SPL, spectrum = vortex_noise(T_perRotor=T_perRotor,R=R,VT=VT,s=s,
			Cl_mean=Cl_mean,N=N,B=B,delta_S=delta_S,h=0*ureg.ft,t_c=t_c,St=0.28,
			weighting="None")
		configs[config][case]["SPL"] = SPL
		configs[config][case]["f_{peak}"] = f_peak

		#A-weighted
		f_peak, SPL, spectrum = vortex_noise(T_perRotor=T_perRotor,R=R,VT=VT,s=s,
			Cl_mean=Cl_mean,N=N,B=B,delta_S=delta_S,h=0*ureg.ft,t_c=t_c,St=0.28,
			weighting="A")
		configs[config][case]["SPL_A"] = SPL
		

# Plotting commands
plt.ion()
fig1 = plt.figure(figsize=(12,12), dpi=80)
plt.rc('axes', axisbelow=True)
plt.show()

y_pos = np.arange(len(configs))
labels = [""]*len(configs)
for i, config in enumerate(configs):
	labels[i] = config

xmin = np.min(y_pos) - 0.7
xmax = np.max(y_pos) + 0.7

offset_array = [-0.3,0,0.3]
width = 0.2
colors = ["grey", "w", "k"]


#Maximum takeoff weight
plt.subplot(2,2,1)
for i,config in enumerate(configs):
	for j,case in enumerate(configs[config]):
		c = configs[config][case]
		offset = offset_array[j]
		MTOW = c["MTOW"].to(ureg.lbf).magnitude

		if (i == 0):
			plt.bar(i+offset,MTOW,align='center',alpha=1,width=width,color=colors[j],
				label=case)
		else:
			plt.bar(i+offset,MTOW,align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Weight (lbf)', fontsize = 16)
plt.xlim(xmin=xmin,xmax=xmax)
[ymin,ymax] = plt.gca().get_ylim()
plt.ylim(ymax = 1.1*ymax)
plt.title("Maximum Takeoff Weight",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)


#Trip cost per passenger 
plt.subplot(2,2,2)
for i,config in enumerate(configs):
	for j,case in enumerate(configs[config]):
		c = configs[config][case]
		offset = offset_array[j]
		cptpp = c["cost_per_trip_per_passenger"]

		if (i == 0):
			plt.bar(i+offset,cptpp,align='center',alpha=1,width=width,color=colors[j],
				label=case)
		else:
			plt.bar(i+offset,cptpp,align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xlim(xmin=xmin,xmax=xmax)
[ymin,ymax] = plt.gca().get_ylim()
plt.ylim(ymax = 1.1*ymax)
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Cost ($US)', fontsize = 16)
plt.title("Cost per Trip, per Passenger",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)

#Vortex-noise peak frequency (in hover, sizing mission) 
plt.subplot(2,2,3)
for i,config in enumerate(configs):
	for j,case in enumerate(configs[config]):
		c = configs[config][case]
		offset = offset_array[j]
		f_peak = c["f_{peak}"].to(ureg.turn/ureg.s).magnitude

		if (i == 0):
			plt.bar(i+offset,f_peak,align='center',alpha=1,width=width,color=colors[j],
				label=case)
		else:
			plt.bar(i+offset,f_peak,align='center',alpha=1,width=width,color=colors[j])


plt.grid()
plt.yscale('log')
plt.xlim(xmin=xmin,xmax=xmax)
[ymin,ymax] = plt.gca().get_ylim()
plt.ylim(ymax=ymax*5)
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Frequency (Hz)', fontsize = 16)
plt.title("Vortex-Noise Peak Frequency",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)


#Sound pressure level (in hover, sizing mission) 
plt.subplot(2,2,4)
for i,config in enumerate(configs):
	for j,case in enumerate(configs[config]):
		c = configs[config][case]
		offset = offset_array[j]
		SPL_sizing = c["SPL_A"]

		if (i == 0):
			plt.bar(i+offset,SPL_sizing,align='center',alpha=1,width=width,color=colors[j],
				label=case)
		else:
			plt.bar(i+offset,SPL_sizing,align='center',alpha=1,width=width,color=colors[j])

SPL_req = 62
plt.plot([np.min(y_pos)-1,np.max(y_pos)+1],[SPL_req, SPL_req],
	color="black", linewidth=3, linestyle="-")
plt.grid()
plt.xlim(xmin=xmin,xmax=xmax)
[ymin,ymax] = plt.gca().get_ylim()
plt.ylim(ymin = 57,ymax = ymax + 1)
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('SPL (dBA)', fontsize = 16)
plt.title("Sound Pressure Level (sizing mission)",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)


if reserve_type == "FAA_day" or reserve_type == "FAA_night":
	num = solution("t_{loiter}_OnDemandSizingMission").to(ureg.minute).magnitude
	if reserve_type == "FAA_day":
		reserve_type_string = "FAA day VFR (%0.0f-minute loiter time)" % num
	elif reserve_type == "FAA_night":
		reserve_type_string = "FAA night VFR (%0.0f-minute loiter time)" % num
elif reserve_type == "Uber":
	num = solution["constants"]["R_{divert}_OnDemandSizingMission"].to(ureg.nautical_mile).magnitude
	reserve_type_string = " (%0.0f-nm diversion distance)" % num


if autonomousEnabled:
	autonomy_string = "autonomy enabled"
else:
	autonomy_string = "pilot required"

title_str = "Aircraft parameters: structural mass fraction = %0.2f; battery energy density = %0.0f Wh/kg; %s\n" \
	% (weight_fraction, C_m.to(ureg.Wh/ureg.kg).magnitude, autonomy_string) \
	+ "Sizing mission (%s): %0.0f passengers; %0.0fs hover time; reserve type = " \
	% (sizing_mission_type, sizing_N_passengers, sizing_t_hover.to(ureg.s).magnitude) \
	+ reserve_type_string + "\n"\
	+ "Revenue mission (%s): %0.1f passengers; %0.0fs hover time; no reserve; charger power = %0.0f kW\n" \
	% (revenue_mission_type, revenue_N_passengers, revenue_t_hover.to(ureg.s).magnitude, charger_power.to(ureg.kW).magnitude) \
	+ "Deadhead mission (%s): %0.1f passengers; %0.0fs hover time; no reserve; deadhead ratio = %0.1f" \
	% (deadhead_mission_type, deadhead_N_passengers, deadhead_t_hover.to(ureg.s).magnitude, deadhead_ratio)

plt.suptitle(title_str,fontsize = 13.5)
plt.tight_layout()
plt.subplots_adjust(left=0.08,right=0.98,bottom=0.10,top=0.87)
plt.savefig('low_noise_design_plot_01.pdf')