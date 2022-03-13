export class Role {
    static readonly ADMIN = new Role("ROLE_ADMIN", "Admin");
    static readonly AICREATOR = new Role("ROLE_AICREATOR", "AI Creator");
    static readonly AITESTER = new Role("ROLE_AITESTER", "AI Tester");

    public static rolesById: { [id: string]: string; } = [Role.ADMIN, Role.AICREATOR, Role.AITESTER].reduce(function (map, obj) {
        map[obj.id] = obj.name;
        return map;
    }, {});

    public id: string;
    public name: string;

    constructor(id: string, name: string) {
        this.id = id;
        this.name = name;
    }
}