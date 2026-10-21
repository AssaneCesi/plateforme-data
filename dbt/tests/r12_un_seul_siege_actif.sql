{{ config(
    severity='warn',
    store_failures=true,
    meta={
        'regle_id': 'R12',
        'denominateur_modele': 'stg_unites_legales',
        'denominateur_filtre': "etat_administratif = 'A'"
    }
) }}

-- R12 : une unité légale active doit avoir exactement un siège actif.
-- Règle « à valider avec le métier » : les données réelles contiennent des cas légitimes
-- (transfert de siège en cours, par exemple). D'où la sévérité warn et un seuil non nul.
--
-- Piège de périmètre : si on ne charge qu'un département, le siège de certaines
-- entreprises est ailleurs. On ne contrôle donc que les unités dont le siège déclaré
-- (nic_siege) fait partie des établissements chargés.

with sieges_actifs as (
    select siren, count(*) as nb
    from {{ ref('stg_etablissements') }}
    where est_siege and etat_administratif = 'A'
    group by siren
)

select ul.siren, coalesce(s.nb, 0) as nb_sieges_actifs
from {{ ref('stg_unites_legales') }} as ul
left join sieges_actifs as s using (siren)
where ul.etat_administratif = 'A'
  and ul.siren || ul.nic_siege in (select siret from {{ ref('stg_etablissements') }})
  and coalesce(s.nb, 0) <> 1
