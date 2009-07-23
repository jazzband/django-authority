BEGIN;
-- Application: authority
-- Model: Permission
ALTER TABLE "authority_permission"
	ADD "date_requested" timestamp with time zone;
ALTER TABLE "authority_permission"
	ADD "approved" boolean;
ALTER TABLE "authority_permission"
	ADD "date_approved" timestamp with time zone;
UPDATE "authority_permission"
	SET "approved" = True;
UPDATE "authority_permission"
	SET "date_approved" = NOW();
COMMIT;
