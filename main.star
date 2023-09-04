def run(plan):
	requirement_artifact = plan.upload_files(
		src='github.com/galenmarchetti/analytics-tooling/app',
	)

	hn_data_puller = plan.add_service(
		"hn-data-puller",
		config=ServiceConfig(
			"python:3.11.5-bullseye",
			files={
				"/app": requirement_artifact, 
			},
			ports = {
				"streamlit": PortSpec(
					8501,
					wait = None
				)
			}
		),
	)

	plan.exec(
		hn_data_puller.name,
		recipe=ExecRecipe(
			["pip", "install", "-r", "/app/requirements.txt"])
	)

	plan.exec(
		hn_data_puller.name,
		recipe=ExecRecipe(
			["python", "/app/pull_hn_data.py"])
	)

	plan.exec(
		hn_data_puller.name,
		recipe=ExecRecipe(
			["streamlit", "run", "/app/streamlit_from_csv.py"])
	)
