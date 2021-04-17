find ./user_data -type d -name 'data_*' | while read file; do 
  [ "${file#./user_data/data_}" -gt 10000 ] && rm -r "$file" 
done
