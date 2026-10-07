import { escapeHtml, validateContactForm } from "./contact.utils";

const valid = {
  lastname: " Dupont ",
  firstname: "Jean-Pierre",
  phone: "06 12 34 56 78",
  email: "Jean.Dupont@Example.fr",
  consentResults: true,
  consentCommunications: false,
};

describe("validateContactForm", () => {
  it("accepts and normalizes a valid form", () => {
    const { data, errors } = validateContactForm(valid);
    expect(errors).toBeUndefined();
    expect(data).toEqual({
      ...valid,
      lastname: "Dupont",
      email: "jean.dupont@example.fr",
    });
  });

  it("accepts an empty phone and international format", () => {
    expect(validateContactForm({ ...valid, phone: "" }).errors).toBeUndefined();
    expect(
      validateContactForm({ ...valid, phone: "+33 6 12 34 56 78" }).errors
    ).toBeUndefined();
  });

  it("accepts names with accents and apostrophes", () => {
    expect(
      validateContactForm({ ...valid, lastname: "O'Brien", firstname: "Élodie" })
        .errors
    ).toBeUndefined();
  });

  it("requires the results consent", () => {
    const { errors } = validateContactForm({ ...valid, consentResults: false });
    expect(errors?.consentResults).toBeDefined();
  });

  it("only accepts real booleans for consents", () => {
    const { errors } = validateContactForm({ ...valid, consentResults: "true" });
    expect(errors?.consentResults).toBeDefined();
  });

  it("rejects invalid values and HTML", () => {
    const { errors } = validateContactForm({
      ...valid,
      lastname: "<a href='x'>clic</a>",
      firstname: "",
      phone: "123",
      email: "pas-un-email",
    });
    expect(Object.keys(errors ?? {}).sort()).toEqual(
      ["email", "firstname", "lastname", "phone"].sort()
    );
  });

  it("handles missing input", () => {
    expect(validateContactForm(undefined).errors).toBeDefined();
  });
});

describe("escapeHtml", () => {
  it("escapes HTML special characters", () => {
    expect(escapeHtml(`<b>"O'Brien" & co</b>`)).toBe(
      "&lt;b&gt;&quot;O&#39;Brien&quot; &amp; co&lt;/b&gt;"
    );
  });
});
