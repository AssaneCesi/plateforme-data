{% test luhn_valide(model, column_name) %}
{#-
    R04 : clé de contrôle des SIREN (9 chiffres) et SIRET (14 chiffres).
    Règle générale : Luhn. Exception documentée : les SIRET de La Poste
    (SIREN 356000000), pour lesquels la somme des 14 chiffres doit être un multiple de 5.
    Un test dbt renvoie les lignes EN ÉCHEC.
-#}

with valeurs as (
    select distinct {{ column_name }} as valeur
    from {{ model }}
    where {{ column_name }} is not null
      and regexp_full_match({{ column_name }}, '[0-9]+')
),

chiffres as (
    select
        v.valeur,
        length(v.valeur)                                  as n,
        g.i                                               as position,
        cast(substring(v.valeur, g.i, 1) as integer)      as d
    from valeurs as v
    cross join generate_series(1, 14) as g(i)
    where g.i <= length(v.valeur)
),

scores as (
    select
        valeur,
        sum(case when (n - position) % 2 = 1
                 then case when d * 2 > 9 then d * 2 - 9 else d * 2 end
                 else d end)                              as total_luhn,
        sum(d)                                            as somme_chiffres
    from chiffres
    group by valeur
)

select valeur
from scores
where case
        when length(valeur) = 14 and valeur like '356000000%' then somme_chiffres % 5 <> 0
        else total_luhn % 10 <> 0
      end

{% endtest %}
