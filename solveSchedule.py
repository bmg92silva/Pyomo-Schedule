# %%
# libraries
import os
import sqlite3
import pandas as pd

from pyomo.environ import *
from pyomo.opt import SolverFactory
from pyomo import environ as pym

from IPython.display import display
from collections import defaultdict


def mainSched():
    # %%

    # Connect to db
    #conn = sqlite3.connect("db/full")
    conn = sqlite3.connect("db/lite")

    # Set Variables
    # Days a Week
    days = "Mon Tue Wed Thu Fri Sat".split()

    # Blocks of each day
    blocks = "AM1 AM2 PM1 PM2".split()  # 4 blocks of 2 hours each

    df_rooms = pd.read_sql_query(f"SELECT * FROM rooms", conn)
    classrooms = df_rooms.iloc[:, 0].tolist()

    df_group = pd.read_sql_query(f"SELECT * FROM groups", conn)
    groups = df_group.iloc[:, 0].tolist()

    df_prof = pd.read_sql_query(f"SELECT * FROM profs", conn)
    professors = df_prof.iloc[:, 0].tolist()

    df_ucs = pd.read_sql_query(f"SELECT * FROM ucs", conn)
    ucs = df_ucs.iloc[:, 0].tolist()
    
    df_const = pd.read_sql_query(f"SELECT * FROM const", conn)
    ucs = df_ucs.iloc[:, 0].tolist()

    # %%
    # Create model and decision variable
    model = ConcreteModel()

    # Decision Variable
    model.lessons = Var(
        days, blocks, classrooms, groups, professors, ucs, within=Binary, initialize=0
    )

    # %%
    # Define objective function

    # Set the weight for each day of the week
    day_weights = {
        "Mon": 10000,
        "Tue": 1000,
        "Wed": 100,
        "Thu": 10,
        "Fri": 1,
        "Sat": 0,
        "Sun": 0,
    }
    # Set the weight for each block
    block_weights = {"AM1": 4, "AM2": 3, "PM1": 2, "PM2": 1}

 
    def objective_rule(model):
        lessonsSum = 0
        size_G_values = df_group.set_index('group_id')['group_size'].to_dict()
        size_CR_values = df_rooms.set_index('room_id')['room_size'].to_dict()
        
        for day in days:
            day_weight = day_weights[day]
            for block in blocks:
                block_weight = block_weights[block]
                for classroom in classrooms:
                    size_CR = size_CR_values.get(classroom, 0)
                    for group in groups:
                        size_G = size_G_values.get(group, 0)
                        room_size_bonus = 40 - (size_CR - size_G)
                        if size_G > size_CR: room_size_bonus = 1
                        for professor in professors:
                            for uc in ucs:
                                lessonsSum += (
                                    day_weight
                                    * block_weight
                                    * room_size_bonus
                                    * model.lessons[
                                        day, block, classroom, group, professor, uc
                                    ]
                                )

        return lessonsSum

    model.obj = Objective(rule=objective_rule, sense=maximize)

    # %%
    # General Constraints

    # Constraint for each group have a max of 2 classes from the same UC in a week
    value_C1 = df_const.loc[df_const['const_id'] == 'C1', 'const_value'].values[0]
    def max_lessons_per_uc_group_rule(model, group, uc):
        lessons_sum = 0
        for day in days:
            for block in blocks:
                for classroom in classrooms:
                    for professor in professors:
                        lessons_sum += model.lessons[
                            day, block, classroom, group, professor, uc
                        ]

        return lessons_sum <= value_C1

    model.max_lessons_per_uc_group = Constraint(
        groups, ucs, rule=max_lessons_per_uc_group_rule
    )

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    # Constraint for at most one lesson per day, block, and classroom
    def max_one_lesson_per_slot_rule(model, day, block, classroom):
        lessons_sum = 0
        for group in groups:
            for professor in professors:
                for uc in ucs:
                    lessons_sum += model.lessons[
                        day, block, classroom, group, professor, uc
                    ]

        return lessons_sum <= 1

    model.max_one_lesson_per_slot = Constraint(
        days, blocks, classrooms, rule=max_one_lesson_per_slot_rule
    )

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    # Constraint for a group not having two lessons simultaneously
    def no_simultaneous_lessons_group_rule(model, group, day, block):
        lessons_sum = 0
        for classroom in classrooms:
            for professor in professors:
                for uc in ucs:
                    lessons_sum += model.lessons[
                        day, block, classroom, group, professor, uc
                    ]

        return lessons_sum <= 1

    model.no_simultaneous_lessons_group = Constraint(
        groups, days, blocks, rule=no_simultaneous_lessons_group_rule
    )

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    # Constraint for a professor not having two lessons simultaneously
    def no_simultaneous_lessons_professor_rule(model, professor, day, block):
        lessons_sum = 0
        for classroom in classrooms:
            for group in groups:
                for uc in ucs:
                    lessons_sum += model.lessons[
                        day, block, classroom, group, professor, uc
                    ]
        return lessons_sum <= 1

    model.no_simultaneous_lessons_professor = Constraint(
        professors, days, blocks, rule=no_simultaneous_lessons_professor_rule
    )

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    # Constraint for a maximum of 15 lessons (30 hours) per week for each professor
    value_C2 = df_const.loc[df_const['const_id'] == 'C2', 'const_value'].values[0]
    def max_lessons_per_week_professor_rule(model, professor):
        lessons_sum = 0
        for day in days:
            for block in blocks:
                for classroom in classrooms:
                    for group in groups:
                        for uc in ucs:
                            lessons_sum += model.lessons[
                                day, block, classroom, group, professor, uc
                            ]

        return lessons_sum <= value_C2

    model.max_lessons_per_week_professor = Constraint(
        professors, rule=max_lessons_per_week_professor_rule
    )

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    # Constraint for a maximum of 3 lessons (6 hours) per day for each professor
    value_C3 = df_const.loc[df_const['const_id'] == 'C3', 'const_value'].values[0]
    def max_lessons_per_day_professor_rule(model, professor, day):
        lessons_sum = 0
        for block in blocks:
            for classroom in classrooms:
                for group in groups:
                    for uc in ucs:
                        lessons_sum += model.lessons[
                            day, block, classroom, group, professor, uc
                        ]

        return lessons_sum <= value_C3

    model.max_lessons_per_day_professor = Constraint(
        professors, days, rule=max_lessons_per_day_professor_rule
    )

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    # Constraint to not repeat UC in the same day
    def not_repeat_uc_same_day_rule(model, day, group, uc):
        lessons_sum = 0
        for block in blocks:
            for classroom in classrooms:
                for professor in professors:
                    lessons_sum += model.lessons[
                        day, block, classroom, group, professor, uc
                    ]

        return lessons_sum <= 1
    
    value_C4 = df_const.loc[df_const['const_id'] == 'C4', 'const_value'].values[0]
    if value_C4 == 1:
        model.not_repeat_uc_same_day = Constraint(
            days, groups, ucs, rule=not_repeat_uc_same_day_rule
        )

    # %%
    # Constraints for days without classes for groups

    df_days_group = pd.read_sql_query("SELECT * FROM days_groups", conn)
    group_days_mapping = defaultdict(list)

    for index, row in df_days_group.iterrows():
        group_days_mapping[row["group_id"]].extend(row["days"].split(";"))

    def days_group_constraint_rule(model, day, block, classroom, group, professor, uc):
        if group in group_days_mapping:
            for daysGroup in group_days_mapping[group]:
                days_group_split = daysGroup.split()
                if day in days_group_split and block in days_group_split[1:]:
                    return (
                        model.lessons[day, block, classroom, group, professor, uc] == 0
                    )
        return Constraint.Skip

    model.days_group_constraint = Constraint(
        days,
        blocks,
        classrooms,
        groups,
        professors,
        ucs,
        rule=days_group_constraint_rule,
    )

    # %%
    # Constraints for days without classes for professors

    df_days_prof = pd.read_sql_query("SELECT * FROM days_profs", conn)
    prof_days_mapping = defaultdict(list)

    for index, row in df_days_prof.iterrows():
        prof_days_mapping[row["prof_id"]].extend(row["days"].split(";"))

    def days_prof_constraint_rule(model, day, block, classroom, group, professor, uc):
        if professor in prof_days_mapping:
            for daysProf in prof_days_mapping[professor]:
                days_prof_split = daysProf.split()
                if day in days_prof_split and block in days_prof_split[1:]:
                    return (
                        model.lessons[day, block, classroom, group, professor, uc] == 0
                    )
        return Constraint.Skip

    model.days_prof_constraint = Constraint(
        days,
        blocks,
        classrooms,
        groups,
        professors,
        ucs,
        rule=days_prof_constraint_rule,
    )

    # %%
    # Constraints for rooms and ucs

    df_room_uc = pd.read_sql_query("SELECT * FROM rooms_ucs", conn)

    uc_rooms_mapping = {}
    for uc_id, uc_rooms in df_room_uc.groupby("uc_id")["rooms"]:
        uc_rooms_mapping[uc_id] = set(";".join(uc_rooms).split())

    def room_uc_constraint_rule(model, day, block, group, classroom, professor, uc):
        if uc in uc_rooms_mapping:
            if classroom in uc_rooms_mapping[uc]:
                return Constraint.Skip
            return model.lessons[day, block, classroom, group, professor, uc] == 0
        return Constraint.Skip

    model.room_uc_constraint = Constraint(
        days, blocks, groups, classrooms, professors, ucs, rule=room_uc_constraint_rule
    )

    # %%
    # Constraints for groups and ucs

    df_group_uc = pd.read_sql_query("SELECT * FROM groups_ucs", conn)
    group_uc_map = (
        df_group_uc.groupby("group_id")["ucs"]
        .apply(lambda x: set(";".join(x).split()))
        .to_dict()
    )

    def group_uc_constraint_rule(model, day, block, group, classroom, professor, uc):
        if uc not in group_uc_map.get(group, set()):
            return model.lessons[day, block, classroom, group, professor, uc] == 0
        else:
            return Constraint.Skip

    model.group_uc_constraint = Constraint(
        days, blocks, groups, classrooms, professors, ucs, rule=group_uc_constraint_rule
    )

    # %%
    # Constraints for professors and groups/ucs

    df_prof_uc = pd.read_sql_query(f"SELECT * FROM profs_ucs", conn)

    prof_uc_dict = {}
    for index, row in df_prof_uc.iterrows():
        prof_id = row["prof_id"]
        profUC = row["ucs"].split(";")
        prof_uc_dict[prof_id] = [uc.split() for uc in profUC]

    def professor_group_uc_constraint_rule(
        model, day, block, classroom, group, professor, uc
    ):
        prof_uc_list = prof_uc_dict.get(professor, [])
        for prof_uc in prof_uc_list:
            if group in prof_uc[0] and uc in prof_uc[1:]:
                return Constraint.Skip
        return model.lessons[day, block, classroom, group, professor, uc] == 0

    model.professor_group_uc_constraint = Constraint(
        days,
        blocks,
        classrooms,
        groups,
        professors,
        ucs,
        rule=professor_group_uc_constraint_rule,
    )

    # %%
    # Constraints for Class Room size

    group_sizes = dict(zip(df_group['group_id'], df_group['group_size']))
    room_sizes = dict(zip(df_rooms['room_id'], df_rooms['room_size']))

    def class_room_size_constraint_rule(model, day, block, classroom, group, professor, uc):
        num_students = group_sizes[group]
        seats_room = room_sizes[classroom]
        if num_students > seats_room:
            return model.lessons[day, block, classroom, group, professor, uc] == 0
        else:
            return Constraint.Skip

    value_C5 = df_const.loc[df_const['const_id'] == 'C5', 'const_value'].values[0]
    if value_C5 == 1:
        model.class_room_size_constraint = Constraint(days, blocks, classrooms, groups, professors, ucs, rule=class_room_size_constraint_rule)

    # %%
    
    # Solve the problem
    opt = SolverFactory("gurobi")
    results = opt.solve(model)

    # opt = SolverFactory('CPLEX')
    # os.environ['NEOS_EMAIL'] = 'a20811@alunos.ipca.pt'
    # solver_manager = SolverManagerFactory('neos')
    # results = solver_manager.solve(model, opt=opt)

    # %%
    # Dictionary to store the results for each group

    all_results = {}
    groupList = []
    groupsList_ID = []

    for group in groups:
        result_data = []
        for block in blocks:
            block_data = {"Block": block}
            for day in days:
                schedule_info = []
                for classroom in classrooms:
                    for professor in professors:
                        for uc in ucs:
                            if (
                                value(
                                    model.lessons[
                                        day, block, classroom, group, professor, uc
                                    ]
                                )
                                == 1
                            ):
                                schedule_info.append(f"{uc}-{classroom}-{professor}")
                block_data[day] = ",".join(schedule_info)
            result_data.append(block_data)

        # Convert the result_data list to a DataFrame
        result_df = pd.DataFrame(result_data)
        print(group)
        display(result_df)
        groupList.append(result_df)
        groupsList_ID.append(group)

        # Store the DataFrame in the dictionary using the group as key
        all_results[group] = result_df

    # Save Excel
    static_folder = os.path.join(os.getcwd(), "static")
    excel_folder = os.path.join(static_folder, "excel")
    if not os.path.exists(excel_folder):
        os.makedirs(excel_folder)

    with pd.ExcelWriter(os.path.join(excel_folder, 'schedule_groups.xlsx')) as writer:
        for group, result_df in all_results.items():
            result_df.to_excel(writer, sheet_name=f"Schedule_{group}", index=False)

    # %%
    # Dictionary to store the results for each professor

    all_results = {}
    profList = []
    profList_ID = []

    for professor in professors:
        result_data = []
        for block in blocks:
            block_data = {"Block": block}
            for day in days:
                schedule_info = []
                for classroom in classrooms:
                    for group in groups:
                        for uc in ucs:
                            if (
                                value(
                                    model.lessons[
                                        day, block, classroom, group, professor, uc
                                    ]
                                )
                                == 1
                            ):
                                schedule_info.append(f"{uc}-{classroom}-{group}")
                block_data[day] = ",".join(schedule_info)
            result_data.append(block_data)

        # Convert the result_data list to a DataFrame
        result_df = pd.DataFrame(result_data)
        print(professor)
        display(result_df)
        profList.append(result_df)
        profList_ID.append(professor)

        # Store the DataFrame in the dictionary using the professor as the key
        all_results[professor] = result_df

    # Save Excel
    with pd.ExcelWriter(os.path.join(excel_folder, 'schedule_professors.xlsx')) as writer:
        for professor, result_df in all_results.items():
            result_df.to_excel(writer, sheet_name=f'Schedule_{professor}', index=False)

    return groupList, profList, groupsList_ID, profList_ID
