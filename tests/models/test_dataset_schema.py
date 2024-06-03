import ddeutil.io.models.datasets.db as db


def test_schema_parser():
    schema = db.Scm.model_validate(
        {
            "name": "data_mart",
            "tables": [
                {
                    "name": "customer_master",
                    "features": [
                        {
                            "name": "id",
                            "dtype": "integer",
                            "pk": True,
                        },
                        {
                            "name": "name",
                            "dtype": "varchar( 256 )",
                            "nullable": False,
                        },
                    ],
                },
            ],
        }
    )
    assert schema.name == "data_mart"
    assert len(schema.tables) == 1
    assert schema.tables[0].name == "customer_master"
