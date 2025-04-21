import pandas as pd
from typing import List, Dict, Tuple, Any

def load_csv(file_path: str) -> pd.DataFrame:
    """Load CSV file into a pandas DataFrame."""
    return pd.read_csv(file_path)

def find_missing_data(df: pd.DataFrame) -> Dict[int, List[str]]:
    """
    Find rows with missing data and identify which columns are missing.
    
    Returns a dictionary with row indices as keys and lists of missing columns as values.
    """
    missing_data = {}
    for idx, row in df.iterrows():
        missing_cols = row.index[row.isna()].tolist()
        if missing_cols:
            missing_data[idx] = missing_cols
    return missing_data

def find_similar_rows(target_row: pd.Series, reference_df: pd.DataFrame, match_columns: List[str]) -> pd.DataFrame:
    """
    Find rows in the reference DataFrame that match the target row on specified columns.
    
    Args:
        target_row: Row with missing data
        reference_df: DataFrame to search in
        match_columns: Columns to use for matching
        
    Returns:
        DataFrame with matching rows
    """
    # Abordagem mais flexível: priorizamos correspondências em colunas importantes,
    # mas não exigimos que todas correspondam
    
    # Filtro inicial por código NCM e país de origem quando disponíveis
    filtered_df = reference_df.copy()
    
    # Aplicar filtros de alta prioridade, se disponíveis
    if 'ncm_code' in target_row.index and not pd.isna(target_row['ncm_code']):
        filtered_df = filtered_df[filtered_df['ncm_code'] == target_row['ncm_code']]
    
    if len(filtered_df) > 0 and 'country_origin_acronym' in target_row.index and not pd.isna(target_row['country_origin_acronym']):
        filtered_df = filtered_df[filtered_df['country_origin_acronym'] == target_row['country_origin_acronym']]
    
    # Se temos muitos resultados (>20), podemos aplicar filtros adicionais
    if len(filtered_df) > 20:
        # Filtrar por modo de transporte, se disponível
        if 'transport_mode_pt' in target_row.index and not pd.isna(target_row['transport_mode_pt']):
            trans_filtered = filtered_df[filtered_df['transport_mode_pt'] == target_row['transport_mode_pt']]
            # Só aplicamos o filtro se ele não reduzir demais os resultados
            if len(trans_filtered) > 5:
                filtered_df = trans_filtered
        
        # Filtrar por local de desembaraço, se disponível
        if len(filtered_df) > 20 and 'clearance_place_entry' in target_row.index and not pd.isna(target_row['clearance_place_entry']):
            place_filtered = filtered_df[filtered_df['clearance_place_entry'] == target_row['clearance_place_entry']]
            if len(place_filtered) > 5:
                filtered_df = place_filtered
    
    # Se não encontramos nada com os filtros de alta prioridade, tentamos apenas NCM ou país
    if len(filtered_df) == 0:
        if 'ncm_code' in target_row.index and not pd.isna(target_row['ncm_code']):
            filtered_df = reference_df[reference_df['ncm_code'] == target_row['ncm_code']]
        
        # Se ainda não temos resultados, tentamos apenas pelo país
        if len(filtered_df) == 0 and 'country_origin_acronym' in target_row.index and not pd.isna(target_row['country_origin_acronym']):
            filtered_df = reference_df[reference_df['country_origin_acronym'] == target_row['country_origin_acronym']]
    
    # Se mesmo assim não encontramos nada, voltamos ao dataframe original
    if len(filtered_df) == 0:
        return pd.DataFrame()
    
    # Calculamos uma pontuação de relevância para cada linha filtrada
    scored_rows = []
    for idx, row in filtered_df.iterrows():
        score = 0
        # Pontuamos com base nas correspondências exatas em cada coluna
        for col in match_columns:
            if col in target_row.index and col in row.index and not pd.isna(target_row[col]) and not pd.isna(row[col]):
                if target_row[col] == row[col]:
                    if col in ['ncm_code', 'country_origin_acronym']:
                        score += 3  # Maior peso para colunas importantes
                    else:
                        score += 1
        
        scored_rows.append((idx, score, row))
    
    # Ordenamos por pontuação (maior primeiro)
    scored_rows.sort(key=lambda x: x[1], reverse=True)
    
    # Pegamos os índices das linhas mais relevantes
    if scored_rows:
        top_indices = [x[0] for x in scored_rows]
        # Retornamos as linhas mais relevantes, limitadas a 10
        return filtered_df.loc[top_indices[:min(10, len(top_indices))]]
    
    return pd.DataFrame()

def prepare_inference_data(row_with_missing: pd.Series, missing_columns: List[str], 
                          similar_rows: pd.DataFrame) -> Dict[str, Any]:
    """
    Prepare data for LLM inference.
    
    Args:
        row_with_missing: The row with missing data
        missing_columns: List of columns with missing data
        similar_rows: DataFrame with similar rows from the reference dataset
        
    Returns:
        Dictionary with data for LLM inference
    """
    return {
        "row_data": row_with_missing.to_dict(),
        "missing_columns": missing_columns,
        "similar_rows": similar_rows.to_dict('records'),
        "column_descriptions": {
            "yearmonth": "Data da importação no formato YYYY-MM-DD",
            "ncm_code": "Código NCM do produto (Nomenclatura Comum do Mercosul)",
            "country_origin_acronym": "Código de duas letras do país de origem da mercadoria (padrão ISO)",
            "transport_mode_pt": "Modo de transporte em português (MARITIMA, AEREA, RODOVIARIA, etc.)",
            "clearance_place_entry": "Local onde a importação foi desembaraçada (porto, aeroporto, etc.)",
            "consignee_code": "Código CNPJ do importador/destinatário (formato XX.XXX.XXX/XXXX-XX)",
            "shipper_name": "Nome da empresa exportadora/remetente da mercadoria",
            "source": "Fonte dos dados (DUIMP - Crawler Complete, DUIMP - Crawler Partial, etc.)"
        }
    } 