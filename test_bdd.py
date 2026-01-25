from ortools.sat.python import cp_model
from connect_database import get_db_connection
import recup
from Front import schedule_generator as sg

# ==================== CHARGEMENT DES DONNÉES ====================

# On ouvre la connexion principale
connection = get_db_connection()

try:
    cursor = connection.cursor(dictionary=True)

    # 1. Récupération de l'année
    cursor.execute("SELECT id FROM years WHERE name = %s", ("2025-2026",))
    year = cursor.fetchone()
    if not year:
        raise ValueError("L'année 2025-2026 n'existe pas dans la base.")
    year_id = year['id']
    print("year_id : ", year_id)

    # 2. Récupération des semestres
    cursor.execute("SELECT semester_number FROM semesters WHERE year_id = %s", (year_id,))
    semesters = cursor.fetchall()
    semester = [s['semester_number'] for s in semesters]
    print("semestres : ", semester)

    # 3. Promotions
    cursor.execute("SELECT name FROM promotions WHERE year_id = %s", (year_id,))
    promotions = cursor.fetchall()
    promotion = [p['name'] for p in promotions]
    print("promotions : ", promotion)

    # 4. Groupes
    cursor.execute("SELECT name FROM `groups`")
    groups = cursor.fetchall()
    group = [g['name'] for g in groups]
    print("groupes : ", group)

    # 5. Enseignements spécifiques (Test)
    cursor.execute("""
        SELECT id, title, apogee_code, tp_hours_initial, td_hours_initial, cm_hours 
        FROM teachings 
        WHERE title IN ('Initiation au management d’une équipe de projet informatique', 'Projet personnel et professionnel')
    """)
    teachings = cursor.fetchall()

    # 6. Enseignants
    cursor.execute("""
        SELECT u.acronym, u.first_name, u.last_name 
        FROM teachers t 
        JOIN users u ON t.user_id = u.id
    """)
    teachers = cursor.fetchall()

    # 7. Salles
    cursor.execute("SELECT name, seat_capacity FROM rooms")
    rooms_data = cursor.fetchall()
    room = [r['name'] for r in rooms_data]
    print("salles : ", room)

    # 8. Semaines
    cursor.execute("SELECT week_number, start_date, end_date FROM weeks WHERE year_id = %s", (year_id,))
    weeks = cursor.fetchall()
    week = [w['week_number'] for w in weeks]
    print("semaines : ", week)

    # 9. Slots existants et Slots/Teachers
    cursor.execute("SELECT * FROM slots")
    slots_bdd = cursor.fetchall()

    cursor.execute("SELECT * FROM slots_teachers")
    slots_teachers = cursor.fetchall()

    # 10. Types de cours (CM/TD/TP)
    cursor.execute("SELECT acronym FROM slot_types where acronym = 'CM'")
    CM = cursor.fetchall()
    cours_CM = [cm['acronym']+str(i+1) for cm in CM for i in range(5)]
    print("cours CM :", cours_CM)

    cursor.execute("SELECT acronym FROM slot_types where acronym = 'TD'")
    TD = cursor.fetchall()
    cours_TD = [td['acronym']+str(i+1) for td in TD for i in range(10)]
    print("cours TD :", cours_TD)

    cursor.execute("SELECT acronym FROM slot_types where acronym = 'TP'")
    TP = cursor.fetchall()
    cours_TP = [tp['acronym']+str(i+1) for tp in TP for i in range(20)]
    print("cours TP :", cours_TP)

    # 11. Sous-groupes et tailles
    cursor.execute("SELECT * FROM subgroups")
    subgroups = cursor.fetchall()
    groupes_TP = [g['name'] + subg['name'] for g in groups for subg in subgroups]
    print("groupes TP :", groupes_TP)

    cursor.execute("SELECT promotions.student_amount FROM promotions WHERE promotions.year_id = %s;", (year_id,))
    taille_promo = [tp['student_amount'] for tp in cursor.fetchall()]

    cursor.execute("SELECT `groups`.student_amount, `groups`.name FROM `groups`")
    # Transformation en dictionnaire pour un accès rapide
    taille_groupes = {g['name']: g['student_amount'] for g in cursor.fetchall()}
    print("taille_groupes :", taille_groupes)

    cursor.execute("SELECT subgroups.student_amount, subgroups.name FROM subgroups ")
    # Transformation en dictionnaire
    taille_sous_groupes = {sg['name']: sg['student_amount'] for sg in cursor.fetchall()}
    print("taille_sous_groupes :", taille_sous_groupes)

finally:
    # Fermeture propre de la connexion principale
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'connection' in locals() and connection:
        connection.close()

# ==================== LOGIQUE MÉTIER ====================

# Paramètres généraux
jours = 5
creneaux_par_jour = 20
slots = [(d, s) for d in range(jours) for s in range(creneaux_par_jour)]
nb_slots = len(slots)

def slot_to_time(t:float):
    h = 8 + (t // 2)
    m = 30 * (t % 2)
    h_end = 8 + ((t + 1) // 2)
    m_end = 30 * ((t + 1) % 2)
    return f"{h:02d}:{m:02d}-{h_end:02d}:{m_end:02d}"

midi_window = list(range(8, 12))  # 12:00-14:00

# Construction de la liste des cours
cours: list[dict[str, list[str]]] = []
cours_CM_list = []
cours_TD_list = []
cours_TP_list = []
duree_cours = {}

# --- CONNEXION SECONDAIRE POUR LA BOUCLE ---
# On ouvre une nouvelle connexion dédiée à la boucle pour éviter les conflits de curseurs
conn_loop = get_db_connection()
cursor_loop = conn_loop.cursor(dictionary=True)

try:
    for group in slots_bdd:
        nom_ressource_a_ecrire = ""
        year_group = ""
        
        if group['type_id'] == 1: # CM
            year = int(group['promotion_id'])
            year_group = recup.recup_year_group_test_CM(year)
            id_ressource = group['teaching_id']
            
            cursor_loop.execute("SELECT title FROM teachings WHERE id = %s", (id_ressource,))
            nom_ressource = cursor_loop.fetchall()
            
            if nom_ressource:
                year_groupv1 = "_" + year_group
                nom_ressource_a_ecrire = nom_ressource[0]['title'] + year_groupv1
                cours.append({"id": f"Cours_{nom_ressource_a_ecrire}", "groups": [year_group]})
                
                # Récupération de la durée
                cursor_loop.execute("SELECT duration FROM slots WHERE teaching_id = %s AND type_id = 1", (id_ressource,))
                duration1 = cursor_loop.fetchall()
                if duration1:
                    duree_cours[f"Cours_{nom_ressource_a_ecrire}"] = int(2 * duration1[0]['duration'])
                
                cours_CM_list.append(nom_ressource_a_ecrire)

        elif group['type_id'] == 2: # TD
            year = int(group['group_id'])
            id_ressource = group['teaching_id']
            year_group = recup.recup_year_group_test_TD(year)
            
            cursor_loop.execute("SELECT title FROM teachings WHERE id = %s", (id_ressource,))
            nom_ressource = cursor_loop.fetchall()
            
            if nom_ressource:
                year_groupv1 = "_" + year_group
                nom_ressource_a_ecrire = nom_ressource[0]['title'] + year_groupv1
                cours.append({"id": f"Cours_{nom_ressource_a_ecrire}", "groups": [year_group]})
                cours_TD_list.append(nom_ressource_a_ecrire)

        elif group['type_id'] == 3: # TP
            group_id = int(group['group_id'])
            year = int(group['subgroup_id'])
            id_ressource = group['teaching_id']
            year_group = recup.recup_year_group_test_TP(group_id, year)
            year_groupv1 = "_" + year_group
            
            cursor_loop.execute("SELECT title FROM teachings WHERE id = %s", (id_ressource,))
            nom_ressource = cursor_loop.fetchall()
            
            if nom_ressource:
                nom_ressource_a_ecrire = nom_ressource[0]['title'] + year_groupv1
                cours.append({"id": f"Cours_{nom_ressource_a_ecrire}", "groups": [year_group]})
                cours_TP_list.append(nom_ressource_a_ecrire)

finally:
    # Fermeture propre de la connexion de boucle
    cursor_loop.close()
    conn_loop.close()

print("cours : ", cours)

# Durées par défaut pour TD/TP si non définies plus haut
for g in cours_TD_list + cours_TP_list:
    cid = f"Cours_{g}"
    if cid not in duree_cours:
        duree_cours[cid] = 4

# Salles, profs, contraintes
salles = {r["name"]: r["seat_capacity"] for r in rooms_data}
rooms = list(salles.keys())
nb_rooms = len(rooms)
capacites = [salles[r] for r in rooms]

profs: list[str] = [t['first_name'] + ' ' + t['last_name'] for t in teachers]
nb_profs = len(profs)

course_possible_profs = {}
for c in cours:
    cid = c["id"]
    course_possible_profs[cid] = profs.copy()

# Forbidden start slots
course_forbidden_start = {c["id"]: [] for c in cours}
course_forbidden_start["SpecCourse0"] = [0, 1] # Exemple maintenu

# Soft preferences
max_consecutive_per_group = {g: 2 for g in cours_CM_list + cours_TD_list + cours_TP_list}

# ==================== MODÈLE CP-SAT ====================
model = cp_model.CpModel()

# Variables
start = {}
occ = {}
y = {}
z = {}

for c in cours:
    cid = c["id"]
    # Sécurité si la durée manque
    d = duree_cours.get(cid, 3)

    # starts
    for s in range(nb_slots):
        day, offset = slots[s]
        if offset + d <= creneaux_par_jour:
            start[cid, s] = model.NewBoolVar(f"start_{cid}_{s}")
        else:
            start[cid, s] = None

    # occ variables
    for t in range(nb_slots):
        occ[cid, t] = model.NewBoolVar(f"occ_{cid}_{t}")

    # room/prof assign
    for r in range(nb_rooms):
        y[cid, r] = model.NewBoolVar(f"y_{cid}_{r}")
    for p in range(nb_profs):
        z[cid, p] = model.NewBoolVar(f"z_{cid}_{p}")

    # Constraints: 1 room, 1 prof, 1 start
    model.Add(sum(y[cid, r] for r in range(nb_rooms)) == 1)
    
    # Profs allowed check
    allowed_idx = [profs.index(p) for p in course_possible_profs[cid] if p in profs]
    if allowed_idx:
        model.Add(sum(z[cid, p] for p in allowed_idx) == 1)
    
    starts_list = [start[cid, s] for s in range(nb_slots) if start[cid, s] is not None]
    if starts_list:
        model.Add(sum(starts_list) == 1)
    
    # Link starts -> occ
    for t in range(nb_slots):
        covering_starts = []
        for s in range(nb_slots):
            sv = start[cid, s]
            if sv is None: continue
            
            day_s, offset_s = slots[s]
            day_t, offset_t = slots[t]
            if day_s == day_t and offset_s <= offset_t <= offset_s + d - 1:
                covering_starts.append(sv)
        
        if covering_starts:
            model.Add(sum(covering_starts) == occ[cid, t])
        else:
            model.Add(occ[cid, t] == 0)

# --- Contraintes structurelles ---

# Capacité des salles
for c in cours:
    cid = c["id"]
    groupname = cid.replace("Cours_", "") if cid.startswith("Cours_") else None
    
    # Logique de taille
    taille = 0
    if groupname:
        # Nettoyage simple pour match les clés des dicts
        # (À adapter si la logique de nommage est complexe)
        base_name = groupname.split('_')[0] 
        
        if base_name in taille_groupes:
            taille = taille_groupes[base_name]
        elif base_name in taille_sous_groupes:
            taille = taille_sous_groupes[base_name]
        elif len(taille_promo) > 0: # Fallback CM
            taille = taille_promo[0]
            
    for r in range(nb_rooms):
        if taille > capacites[r]:
            model.Add(y[cid, r] == 0)

# Conflits salles
b = {}
for c in cours:
    cid = c["id"]
    for t in range(nb_slots):
        for r in range(nb_rooms):
            b[cid, t, r] = model.NewBoolVar(f"b_{cid}_{t}_{r}")
            model.AddBoolAnd([occ[cid, t], y[cid, r]]).OnlyEnforceIf(b[cid, t, r])
            model.AddBoolOr([occ[cid, t].Not(), y[cid, r].Not()]).OnlyEnforceIf(b[cid, t, r].Not())

for t in range(nb_slots):
    for r in range(nb_rooms):
        model.Add(sum(b[c["id"], t, r] for c in cours) <= 1)

# Conflits profs
for p_idx in range(nb_profs):
    for t in range(nb_slots):
        prof_and_vars = []
        for c in cours:
            cid = c["id"]
            v = model.NewBoolVar(f"profbusy_{p_idx}_{cid}_{t}")
            model.AddBoolAnd([occ[cid, t], z[cid, p_idx]]).OnlyEnforceIf(v)
            model.AddBoolOr([occ[cid, t].Not(), z[cid, p_idx].Not()]).OnlyEnforceIf(v.Not())
            prof_and_vars.append(v)
        model.Add(sum(prof_and_vars) <= 1)

# Pause midi
group_course_map = {}
all_groups = cours_CM_list + cours_TD_list + cours_TP_list
for g in all_groups:
    group_course_map[g] = [c["id"] for c in cours if g in c["groups"]]

for g, clist in group_course_map.items():
    if clist:
        model.Add(sum(occ[cid, t] for cid in clist for t in midi_window) <= 1)

# --- Soft Constraints ---
viol_forbidden = []
viol_overconsec = []

# Forbidden starts
for c in cours:
    cid = c["id"]
    for s in course_forbidden_start.get(cid, []):
        sv = start[cid, s]
        if sv:
            v = model.NewBoolVar(f"viol_forb_{cid}_{s}")
            model.Add(sv == 1).OnlyEnforceIf(v)
            model.Add(sv == 0).OnlyEnforceIf(v.Not())
            viol_forbidden.append(v)

# Max consécutifs
for g in group_course_map:
    max_blocks = max_consecutive_per_group.get(g, 2)
    max_slots_allowed = max_blocks * 3
    for day in range(jours):
        day_offset = day * creneaux_par_jour
        for start_slot in range(0, creneaux_par_jour - max_slots_allowed):
            window = [day_offset + (start_slot + o) for o in range(max_slots_allowed + 1)]
            v = model.NewBoolVar(f"viol_over_{g}_{day}_{start_slot}")
            
            # Somme occupation
            sum_occ = sum(occ[cid, s] for cid in group_course_map[g] for s in window)
            model.Add(sum_occ >= (max_slots_allowed + 1)).OnlyEnforceIf(v)
            model.Add(sum_occ < (max_slots_allowed + 1)).OnlyEnforceIf(v.Not())
            viol_overconsec.append(v)

model.Minimize(10 * sum(viol_forbidden) + 3 * sum(viol_overconsec))

# ==================== RÉSOLUTION ====================
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

# ==================== AFFICHAGE ====================
def format_course_block(cid, day, start_offset):
    d = duree_cours[cid]
    h0 = 8 + (start_offset // 2)
    m0 = 30 * (start_offset % 2)
    tot_minutes = (h0 * 60 + m0) + d * 30
    hend = tot_minutes // 60
    mend = tot_minutes % 60
    return f"{h0:02d}:{m0:02d}-{hend:02d}:{mend:02d} ({d*30}min)"

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("Solution trouvée (status = ", solver.StatusName(status), ")\n")

    planning = {s: [] for s in range(nb_slots)}
    starts_actual = {}
    
    for c in cours:
        cid = c["id"]
        # Trouver start
        for s in range(nb_slots):
            sv = start[cid, s]
            if sv and solver.Value(sv) == 1:
                starts_actual[cid] = s
                break
        
        if cid not in starts_actual: continue
        
        s_idx = starts_actual[cid]
        
        # Trouver Salle & Prof
        r_str = "--"
        for r in range(nb_rooms):
            if solver.Value(y[cid, r]) == 1:
                r_str = rooms[r]
                break
        
        p_str = "--"
        for p in range(nb_profs):
            if solver.Value(z[cid, p]) == 1:
                p_str = profs[p]
                break
        
        # Remplir planning
        for off in range(duree_cours[cid]):
            planning[s_idx + off].append((cid, r_str, p_str))

    # Affichage Console
    for d in range(jours):
        print(f"=== Jour {d+1} ===")
        for t_in_day in range(creneaux_par_jour):
            global_t = d * creneaux_par_jour + t_in_day
            entries = planning[global_t]
            time_str = slot_to_time(t_in_day)
            
            if entries:
                for (cid, r_str, p_str) in entries:
                    is_start = (cid in starts_actual and starts_actual[cid] == global_t)
                    if is_start:
                        day_idx, offset = slots[global_t]
                        block_info = format_course_block(cid, d, offset)
                        print(f"  {time_str} : {cid} (Salle: {r_str}, Prof: {p_str}) -> Débute: {block_info}")
                    else:
                        print(f"  {time_str} : {cid} (en cours)")
            else:
                print(f"  {time_str} : --")
        print("")

    # Génération des images EDT
    # Assurez-vous que recup.recup_edt est compatible avec ces appels
    try:
        t_A1 = {"A1": {"groupes": ["G1", "G2", "G3", "G1A", "G1B", "G2A", "G2B", "G3A", "G3B"], "cours": []}}
        recup.recup_edt(t_A1, jours, creneaux_par_jour, starts_actual, slots, planning, duree_cours, 0, 3, 0, 6, 1)
        sg.generate_schedule("A1", 1, t_A1["A1"]["groupes"], t_A1["A1"]["cours"])
        print("EDT A1 Généré")

        t_A2 = {"A2": {"groupes": ["G4", "G5", "G4A", "G4B", "G5A", "G5B"], "cours": []}}
        recup.recup_edt(t_A2, jours, creneaux_par_jour, starts_actual, slots, planning, duree_cours, 3, 5, 7, 10, 2)
        # sg.generate_schedule("A2", 1, t_A2["A2"]["groupes"], t_A2["A2"]["cours"])
        
        t_A3 = {"A3": {"groupes": ["G7", "G8", "G7A", "G7B", "G8A"], "cours": []}}
        recup.recup_edt(t_A3, jours, creneaux_par_jour, starts_actual, slots, planning, duree_cours, 5, 7, 12, 16, 3)
        # sg.generate_schedule("A3", 1, t_A3["A3"]["groupes"], t_A3["A3"]["cours"])
        
    except Exception as e:
        print(f"Erreur lors de la génération des images : {e}")

else:
    print("Aucune solution trouvée : status =", solver.StatusName(status))

print("creneaux : ", creneaux_par_jour)