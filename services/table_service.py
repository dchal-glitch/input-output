from core.logging import get_logger

logger = get_logger(__name__)

class TableService:
    def __init__(self):
        pass

    def flatten_io_matrix(self, io_matrix, sector_mapping, demand_mapping, demand_groups):
        """Flatten the IO matrix into a list of dictionaries."""
        sector_keys = list(sector_mapping.keys())
        final_demand_keys = list(demand_mapping.keys())

        # Step 2: Create grouped headers
        grouped_headers = []

        # Intermediate Consumption Group
        grouped_headers.append({
            "title": "Intermediate Consumption",
            "colspan": len(sector_keys) + 1,  # +1 for rowname
            "key": "ic",
            "value": "",
            "columns": ["rowname"] + sector_keys
        })

        # Final Demand and Export groups
        for group_title, columns in demand_groups.items():
            grouped_headers.append({
                "title": group_title,
                "colspan": len(columns),
                "key": group_title.lower().replace(" ", "_"),
                "value": "",
                "columns": columns
            })
        
        data_array = []

        for row_index, row in io_matrix.iterrows():
            row_data = []

            # Add rowname field
            row_data.append({
                "key": "rowname",
                "value": sector_mapping.get(row_index, demand_mapping.get(row_index, row_index)),
                "title": sector_mapping.get(row_index, demand_mapping.get(row_index, row_index))
            })

            for col in io_matrix.columns:
                label = sector_mapping.get(col, demand_mapping.get(col, col))
                row_data.append({
                    "key": col,
                    "value": row[col],
                    "title": label
                })

            data_array.append(row_data)

        output_json = {
            "header": {
                "title": "Input Output Table",
                "key": "input_output",
                "value": "inputOutputData",
                "groupedHeaders": grouped_headers
            },
            "dataArray": data_array
        }

        return output_json