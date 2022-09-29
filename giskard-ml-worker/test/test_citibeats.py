def test_hello(german_credit_data):
      print(german_credit_data)
      assert len(german_credit_data.df) == 1000