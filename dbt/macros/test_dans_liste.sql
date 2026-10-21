{% test dans_liste(model, column_name, valeurs) %}
-- Comme accepted_values, mais renvoie une ligne par enregistrement fautif
-- (accepted_values renvoie une ligne par valeur distincte, ce qui sous-estime le taux d'échec).
select {{ column_name }} as valeur
from {{ model }}
where {{ column_name }} is null
   or {{ column_name }} not in ({% for v in valeurs %}'{{ v }}'{% if not loop.last %}, {% endif %}{% endfor %})
{% endtest %}
