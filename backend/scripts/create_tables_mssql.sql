CREATE TABLE [django_migrations] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [app] nvarchar(255) NOT NULL, [name] nvarchar(255) NOT NULL, [applied] datetimeoffset NOT NULL);
GO
CREATE TABLE [django_content_type] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [app_label] nvarchar(100) NOT NULL, [model] nvarchar(100) NOT NULL);
GO
CREATE TABLE [auth_permission] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [name] nvarchar(255) NOT NULL, [content_type_id] int NOT NULL, [codename] nvarchar(100) NOT NULL);
GO
CREATE TABLE [auth_group] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [name] nvarchar(150) NOT NULL UNIQUE);
GO
CREATE TABLE [auth_group_permissions] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [group_id] int NOT NULL, [permission_id] int NOT NULL);
GO
CREATE TABLE [auth_user] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [password] nvarchar(128) NOT NULL, [last_login] datetimeoffset NULL, [is_superuser] bit NOT NULL, [username] nvarchar(150) NOT NULL UNIQUE, [first_name] nvarchar(150) NOT NULL, [last_name] nvarchar(150) NOT NULL, [email] nvarchar(254) NOT NULL, [is_staff] bit NOT NULL, [is_active] bit NOT NULL, [date_joined] datetimeoffset NOT NULL);
GO
CREATE TABLE [auth_user_groups] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [user_id] int NOT NULL, [group_id] int NOT NULL);
GO
CREATE TABLE [auth_user_user_permissions] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [user_id] int NOT NULL, [permission_id] int NOT NULL);
GO
CREATE TABLE [django_admin_log] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [action_time] datetimeoffset NOT NULL, [user_id] int NOT NULL, [content_type_id] int NULL, [object_id] nvarchar(max) NULL, [object_repr] nvarchar(200) NOT NULL, [action_flag] smallint NOT NULL CONSTRAINT django_admin_log_action_flag_a8637d59_check CHECK ([action_flag] >= 0), [change_message] nvarchar(max) NOT NULL);
GO
CREATE TABLE [django_session] ([session_key] nvarchar(40) NOT NULL PRIMARY KEY, [session_data] nvarchar(max) NOT NULL, [expire_date] datetimeoffset NOT NULL);
GO
CREATE TABLE [migration_intake_submission] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [migration_request_id] nvarchar(32) NOT NULL UNIQUE, [requested_date] nvarchar(64) NOT NULL, [requestor] nvarchar(128) NOT NULL, [status] nvarchar(32) NOT NULL, [project_name] nvarchar(255) NOT NULL, [migration_type] nvarchar(128) NOT NULL, [migration_type_value] nvarchar(64) NOT NULL, [region] nvarchar(16) NOT NULL, [areas] nvarchar(max) NOT NULL CONSTRAINT migration_intake_submission_areas_ab7d1cbc_check CHECK ((ISJSON ("areas") = 1)), [countries] nvarchar(max) NOT NULL CONSTRAINT migration_intake_submission_countries_110376e9_check CHECK ((ISJSON ("countries") = 1)), [area_country_pairs] nvarchar(max) NOT NULL CONSTRAINT migration_intake_submission_area_country_pairs_da36581f_check CHECK ((ISJSON ("area_country_pairs") = 1)), [default_location_strategies] nvarchar(max) NOT NULL CONSTRAINT migration_intake_submission_default_location_strategies_fd6902fe_check CHECK ((ISJSON ("default_location_strategies") = 1)), [custom_location_strategies] nvarchar(max) NOT NULL CONSTRAINT migration_intake_submission_custom_location_strategies_1fc47524_check CHECK ((ISJSON ("custom_location_strategies") = 1)), [location_strategy_custom] bit NOT NULL, [custom_location_strategy_justification] nvarchar(max) NOT NULL, [custom_approval_file_name] nvarchar(255) NOT NULL, [custom_approval_file_size] int NULL CONSTRAINT migration_intake_submission_custom_approval_file_size_88997f40_check CHECK ([custom_approval_file_size] >= 0), [custom_approval_file_type] nvarchar(128) NOT NULL, [function_name] nvarchar(255) NOT NULL, [products] nvarchar(max) NOT NULL CONSTRAINT migration_intake_submission_products_3575de73_check CHECK ((ISJSON ("products") = 1)), [proposed_scope] nvarchar(max) NOT NULL, [language_dependencies] nvarchar(max) NOT NULL CONSTRAINT migration_intake_submission_language_dependencies_a0f36b43_check CHECK ((ISJSON ("language_dependencies") = 1)), [fte_number] nvarchar(8) NOT NULL, [jl2] nvarchar(8) NOT NULL, [jl3] nvarchar(8) NOT NULL, [jl4] nvarchar(8) NOT NULL, [job_level_total] smallint NOT NULL CONSTRAINT migration_intake_submission_job_level_total_0f80d135_check CHECK ([job_level_total] >= 0), [risks] nvarchar(max) NOT NULL, [created_at] datetimeoffset NOT NULL, [updated_at] datetimeoffset NOT NULL);
GO
CREATE TABLE [fpo_mapping] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [l1] nvarchar(128) NOT NULL, [gpl] nvarchar(64) NOT NULL, [l2] nvarchar(128) NOT NULL, [sfpo] nvarchar(128) NOT NULL, [num_business_policy] nvarchar(16) NOT NULL, [l3] nvarchar(128) NOT NULL, [fpo] nvarchar(255) NOT NULL, [risk_link] nvarchar(max) NOT NULL, [control_link] nvarchar(max) NOT NULL, [l4] nvarchar(255) NOT NULL, [activity_type] nvarchar(64) NOT NULL, [sub_process_call_activity] nvarchar(255) NOT NULL, [activity_type_2] nvarchar(64) NOT NULL, [assigned_models_from_l5] nvarchar(255) NOT NULL, [process_level] nvarchar(16) NOT NULL, [process_grouping] nvarchar(32) NOT NULL, [last_change] nvarchar(64) NOT NULL, [guid] nvarchar(64) NOT NULL, [connect_link] nvarchar(max) NOT NULL, [num_automated_activities] nvarchar(16) NOT NULL, [num_system_supported_activities] nvarchar(16) NOT NULL, [num_manual_activities] nvarchar(16) NOT NULL, [num_undefined_activities] nvarchar(16) NOT NULL, [num_sub_process_activities] nvarchar(16) NOT NULL, [num_ms_office_activities] nvarchar(16) NOT NULL, [num_touchpoint_external_parties] nvarchar(16) NOT NULL, [num_risks] nvarchar(16) NOT NULL, [num_controls] nvarchar(16) NOT NULL, [num_manual_controls] nvarchar(16) NOT NULL, [num_business_rules] nvarchar(16) NOT NULL, [report_generation_date] nvarchar(32) NOT NULL, [sharepoint_link_sop] nvarchar(max) NOT NULL, [is_reference] bit NOT NULL);
GO
CREATE TABLE [opportunity_assessment] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [migration_request_id] nvarchar(32) NOT NULL, [product] nvarchar(128) NOT NULL, [owner] nvarchar(128) NOT NULL, [location] nvarchar(128) NOT NULL, [l1] nvarchar(128) NOT NULL, [l2] nvarchar(128) NOT NULL, [l3] nvarchar(128) NOT NULL, [l4] nvarchar(255) NOT NULL, [task_name] nvarchar(255) NOT NULL, [task_description] nvarchar(max) NOT NULL, [upstream] nvarchar(max) NOT NULL, [downstream] nvarchar(max) NOT NULL, [risks_related] nvarchar(max) NOT NULL, [complexity] nvarchar(64) NOT NULL, [sop_iop_exists] nvarchar(128) NOT NULL, [training_time_needed] nvarchar(255) NOT NULL, [recommended_handoff_duration] nvarchar(255) NOT NULL, [task_frequency] nvarchar(255) NOT NULL, [unit_of_measure] nvarchar(128) NOT NULL, [volume_monthly] nvarchar(64) NOT NULL, [task_time_per_unit_min] nvarchar(64) NOT NULL, [area] nvarchar(64) NOT NULL, [gsc_site] nvarchar(128) NOT NULL, [task_found_in_service_catalog] nvarchar(255) NOT NULL, [migratable_to_gsc] nvarchar(255) NOT NULL, [fte_calculation] nvarchar(64) NOT NULL, [created_at] datetimeoffset NOT NULL, [updated_at] datetimeoffset NOT NULL);
GO
CREATE TABLE [product_ownership] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [region] nvarchar(16) NOT NULL, [area] nvarchar(32) NOT NULL, [migration_manager] nvarchar(128) NOT NULL, [created_at] datetimeoffset NOT NULL, [updated_at] datetimeoffset NOT NULL);
GO
CREATE TABLE [gsc_site_mapping] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [region] nvarchar(16) NOT NULL, [area] nvarchar(32) NOT NULL, [supporting_gsc_sites] nvarchar(255) NOT NULL, [all_options] nvarchar(255) NOT NULL, [created_at] datetimeoffset NOT NULL, [updated_at] datetimeoffset NOT NULL);
GO
CREATE TABLE [service_catalogue] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [catalogue] nvarchar(64) NOT NULL, [product] nvarchar(128) NOT NULL, [l1] nvarchar(128) NOT NULL, [l2] nvarchar(128) NOT NULL, [l3] nvarchar(128) NOT NULL, [l4] nvarchar(255) NOT NULL, [current_ownership] nvarchar(64) NOT NULL, [customer] nvarchar(128) NOT NULL, [created_at] datetimeoffset NOT NULL, [updated_at] datetimeoffset NOT NULL);
GO
CREATE TABLE [project_attributes_access] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [email] nvarchar(255) NOT NULL UNIQUE, [is_super_admin] bit NOT NULL, [fpo_mapping] bit NOT NULL, [product_ownership] bit NOT NULL, [gsc_site_mapping] bit NOT NULL, [service_catalogue] bit NOT NULL, [project_gantt] bit NOT NULL, [access_control] bit NOT NULL, [created_at] datetimeoffset NOT NULL, [updated_at] datetimeoffset NOT NULL);
GO
CREATE TABLE [project_gantt_plan] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [project_id] bigint NOT NULL UNIQUE, [migration_request_id] nvarchar(32) NOT NULL, [tasks] nvarchar(max) NOT NULL CONSTRAINT project_gantt_plan_tasks_c4eac3ef_check CHECK ((ISJSON ("tasks") = 1)), [meta] nvarchar(max) NOT NULL CONSTRAINT project_gantt_plan_meta_f0bd4513_check CHECK ((ISJSON ("meta") = 1)), [created_at] datetimeoffset NOT NULL, [updated_at] datetimeoffset NOT NULL);
GO
CREATE INDEX [auth_user_user_permissions_user_id_a95ead1b] ON [auth_user_user_permissions] ([user_id]);
GO
CREATE INDEX [project_gantt_plan_migration_request_id_2314104e] ON [project_gantt_plan] ([migration_request_id]);
GO
ALTER TABLE [auth_user_groups] ADD CONSTRAINT [auth_user_groups_group_id_97559544_fk_auth_group_id] FOREIGN KEY ([group_id]) REFERENCES [auth_group] ([id]);
GO
CREATE INDEX [auth_user_groups_user_id_6a12ed8b] ON [auth_user_groups] ([user_id]);
GO
CREATE INDEX [opportunity_assessment_migration_request_id_d4d99e8a] ON [opportunity_assessment] ([migration_request_id]);
GO
ALTER TABLE [project_gantt_plan] ADD CONSTRAINT [project_gantt_plan_project_id_f3366b40_fk_migration_intake_submission_id] FOREIGN KEY ([project_id]) REFERENCES [migration_intake_submission] ([id]);
GO
CREATE INDEX [auth_group_permissions_group_id_b120cbf9] ON [auth_group_permissions] ([group_id]);
GO
ALTER TABLE [auth_group_permissions] ADD CONSTRAINT [auth_group_permissions_permission_id_84c5c92e_fk_auth_permission_id] FOREIGN KEY ([permission_id]) REFERENCES [auth_permission] ([id]);
GO
CREATE INDEX [auth_group_permissions_permission_id_84c5c92e] ON [auth_group_permissions] ([permission_id]);
GO
CREATE UNIQUE INDEX [django_content_type_app_label_model_76bd3d3b_uniq] ON [django_content_type] ([app_label], [model]) WHERE [app_label] IS NOT NULL AND [model] IS NOT NULL;
GO
ALTER TABLE [auth_group_permissions] ADD CONSTRAINT [auth_group_permissions_group_id_b120cbf9_fk_auth_group_id] FOREIGN KEY ([group_id]) REFERENCES [auth_group] ([id]);
GO
ALTER TABLE [auth_permission] ADD CONSTRAINT [auth_permission_content_type_id_2f476e4b_fk_django_content_type_id] FOREIGN KEY ([content_type_id]) REFERENCES [django_content_type] ([id]);
GO
CREATE INDEX [auth_user_user_permissions_permission_id_1fbb5f2c] ON [auth_user_user_permissions] ([permission_id]);
GO
CREATE UNIQUE INDEX [auth_permission_content_type_id_codename_01ab375a_uniq] ON [auth_permission] ([content_type_id], [codename]) WHERE [content_type_id] IS NOT NULL AND [codename] IS NOT NULL;
GO
CREATE INDEX [opportunity_migrati_ec5253_idx] ON [opportunity_assessment] ([migration_request_id], [l1], [l2], [l3]);
GO
CREATE INDEX [gsc_site_mapping_area_1918321f] ON [gsc_site_mapping] ([area]);
GO
CREATE INDEX [auth_user_groups_group_id_97559544] ON [auth_user_groups] ([group_id]);
GO
CREATE INDEX [fpo_mapping_is_reference_a4b82785] ON [fpo_mapping] ([is_reference]);
GO
ALTER TABLE [django_admin_log] ADD CONSTRAINT [django_admin_log_user_id_c564eba6_fk_auth_user_id] FOREIGN KEY ([user_id]) REFERENCES [auth_user] ([id]);
GO
ALTER TABLE [auth_user_user_permissions] ADD CONSTRAINT [auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id] FOREIGN KEY ([user_id]) REFERENCES [auth_user] ([id]);
GO
CREATE INDEX [django_admin_log_user_id_c564eba6] ON [django_admin_log] ([user_id]);
GO
CREATE UNIQUE INDEX [auth_group_permissions_group_id_permission_id_0cd325b0_uniq] ON [auth_group_permissions] ([group_id], [permission_id]) WHERE [group_id] IS NOT NULL AND [permission_id] IS NOT NULL;
GO
CREATE INDEX [gsc_site_ma_region_5b7743_idx] ON [gsc_site_mapping] ([region], [area]);
GO
CREATE INDEX [service_catalogue_catalogue_6386d884] ON [service_catalogue] ([catalogue]);
GO
CREATE INDEX [django_session_expire_date_a5c62663] ON [django_session] ([expire_date]);
GO
CREATE INDEX [product_ownership_region_c3d10531] ON [product_ownership] ([region]);
GO
CREATE INDEX [service_catalogue_product_ef07a1a6] ON [service_catalogue] ([product]);
GO
ALTER TABLE [auth_user_user_permissions] ADD CONSTRAINT [auth_user_user_permissions_permission_id_1fbb5f2c_fk_auth_permission_id] FOREIGN KEY ([permission_id]) REFERENCES [auth_permission] ([id]);
GO
ALTER TABLE [auth_user_groups] ADD CONSTRAINT [auth_user_groups_user_id_6a12ed8b_fk_auth_user_id] FOREIGN KEY ([user_id]) REFERENCES [auth_user] ([id]);
GO
CREATE INDEX [product_ownership_area_f5512843] ON [product_ownership] ([area]);
GO
CREATE INDEX [service_catalogue_l1_3a3e15b0] ON [service_catalogue] ([l1]);
GO
CREATE INDEX [fpo_mapping_l1_8a6a84_idx] ON [fpo_mapping] ([l1], [l2], [l3]);
GO
CREATE UNIQUE INDEX [auth_user_groups_user_id_group_id_94350c0c_uniq] ON [auth_user_groups] ([user_id], [group_id]) WHERE [user_id] IS NOT NULL AND [group_id] IS NOT NULL;
GO
CREATE INDEX [fpo_mapping_fpo_e12ba5_idx] ON [fpo_mapping] ([fpo]);
GO
CREATE INDEX [django_admin_log_content_type_id_c4bce8eb] ON [django_admin_log] ([content_type_id]);
GO
CREATE INDEX [auth_permission_content_type_id_2f476e4b] ON [auth_permission] ([content_type_id]);
GO
CREATE INDEX [fpo_mapping_guid_2d20866e] ON [fpo_mapping] ([guid]);
GO
CREATE INDEX [service_cat_product_a6a147_idx] ON [service_catalogue] ([product], [l1], [l2], [l3]);
GO
CREATE UNIQUE INDEX [auth_user_user_permissions_user_id_permission_id_14a6b632_uniq] ON [auth_user_user_permissions] ([user_id], [permission_id]) WHERE [user_id] IS NOT NULL AND [permission_id] IS NOT NULL;
GO
CREATE INDEX [product_own_region_3441b8_idx] ON [product_ownership] ([region], [area]);
GO
ALTER TABLE [django_admin_log] ADD CONSTRAINT [django_admin_log_content_type_id_c4bce8eb_fk_django_content_type_id] FOREIGN KEY ([content_type_id]) REFERENCES [django_content_type] ([id]);
GO
CREATE INDEX [service_cat_current_259719_idx] ON [service_catalogue] ([current_ownership]);
GO
CREATE INDEX [product_own_migrati_b86471_idx] ON [product_ownership] ([migration_manager]);
GO
CREATE INDEX [fpo_mapping_sfpo_efe8de_idx] ON [fpo_mapping] ([sfpo]);
GO
CREATE INDEX [gsc_site_mapping_region_70e9bdc0] ON [gsc_site_mapping] ([region]);
GO
