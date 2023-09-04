def run(plan):
	requirement_artifact = plan.upload_files(
		src='github.com/galenmarchetti/analytics-tooling/app',
	)

	hn_data_puller = plan.add_service(
		"hn-data-puller",
		config=ServiceConfig(
			"python:3.11.5-bookworm",
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
			["apt-get", "update", "-y"])
	)

	plan.exec(
		hn_data_puller.name,
		recipe=ExecRecipe(
			["apt-get", "install", "screen", "-y"])
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
		recipe=ExecRecipe([
			"screen",
			"-m",
			"-d",
			"streamlit",
			"run",
			"--server.headless",
			"true",
			"app/streamlit_from_csv.py",
			">",
			"streamlit_logs.log",
			"2>&1",
			"&"])
	)
