import duckdb

MAIN_DIR = "s3://lgaliana/data/geodata-days/"
FILES = [
    "ocs2d_2024_62_multidates_comm_v11.parquet",
    "rpg_pac_2024_62_comm_v11.parquet"
]

con = duckdb.connect()
con.sql("INSTALL spatial")
con.sql("LOAD spatial")

# RPG ------------------------------------------

file = MAIN_DIR + FILES[1]

with open("./sql/common/read.sql", "r") as f:
    sql_template = f.read()

# Injecter la variable Python dans le template
query = sql_template.format(chemin=file)
con.sql(query).columns

with open("./sql/rpg/count_distinct.sql", "r") as f:
    sql_template = f.read()

# Injecter la variable Python dans le template
query = sql_template.format(chemin=file)


with open("./sql/rpg/dico_variables.sql", "r") as f:
    sql_template = f.read()
# Injecter la variable Python dans le template
query = sql_template.format(chemin=file)
con.sql(query)


with open("./sql/rpg/volume_culture.sql", "r") as f:
    sql_template = f.read()
# Injecter la variable Python dans le template
query = sql_template.format(chemin=file, var_culture="culture_d1")
con.sql(query)


with open("./sql/rpg/surface_culture.sql", "r") as f:
    sql_template = f.read()
# Injecter la variable Python dans le template
query = sql_template.format(chemin=file, var_culture="culture_d1", var_geom = "geom")
con.sql(query)


# RPG ------------------------------------------

file = MAIN_DIR + FILES[0]

with open("./sql/common/read.sql", "r") as f:
    sql_template = f.read()

query = sql_template.format(chemin=file, var_culture="culture_d1", var_geom = "geom")
con.sql(query).columns

