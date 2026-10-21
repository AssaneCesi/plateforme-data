{% test respecte_regex(model, column_name, motif) %}
-- La valeur (quand elle est renseignée) doit correspondre entièrement au motif.
select {{ column_name }} as valeur
from {{ model }}
where {{ column_name }} is not null
  and not regexp_full_match({{ column_name }}, '{{ motif }}')
{% endtest %}
