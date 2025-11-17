// Example JavaScript file with intentional naming violations

// Classes should be PascalCase
class userService {  // Violation: should be UserService
    constructor() {
        this.user_count = 0;  // Violation: should be userCount
    }
}

class DataProcessor {  // Correct
    constructor() {
        this.userCount = 0;  // Correct
    }
}

// Functions should be camelCase
function ProcessData() {  // Violation: should be processData
    return {};
}

function fetchUserData() {  // Correct
    return {};
}

const processItems = () => {  // Correct
    return [];
};

// Variables should be camelCase
const UserList = [];  // Violation: should be userList
const itemCount = 0;  // Correct

// Constants should be UPPER_SNAKE_CASE
const MAX_ITEMS = 100;  // Correct
const MinValue = 0;  // Violation: should be MIN_VALUE

