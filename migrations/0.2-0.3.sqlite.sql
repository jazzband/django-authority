BEGIN;
-- Application: authority
-- Model: Permission
ALTER TABLE "authority_permission"
	ADD "date_requested" datetime;
ALTER TABLE "authority_permission"
	ADD "approved" bool;
ALTER TABLE "authority_permission"
	ADD "date_approved" datetime;
UPDATE "authority_permission"
    SET "approved" = 1;
UPDATE "authority_permission"
    SET "date_approved" = DATETIME("NOW");
COMMIT;