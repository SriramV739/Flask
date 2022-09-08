create or replace view random_question as
SELECT 
  game_category.game,    
  game_category.categories,    
  question.title
FROM game_category,    question  
WHERE array_remove(regexp_split_to_array(lower(btrim(game_category.categories, ' '::text)), '[;|:]\s*'::text), ''::text) 
  <@ array_remove(regexp_split_to_array(lower(btrim(question.categories, ' '::text)), '[;|:]\s*'::text), ''::text) 
AND question.status = 'Production'::text  
ORDER BY (random())

----------------

create or replace view source_lookup as 
  SELECT lower(source.name) AS lower,
    source.description
   FROM source
   
   