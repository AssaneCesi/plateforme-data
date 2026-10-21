{% test pas_dans_le_futur(model, column_name) %}
select {{ column_name }} as valeur
from {{ model }}
where {{ column_name }} > current_date
{% endtest %}
