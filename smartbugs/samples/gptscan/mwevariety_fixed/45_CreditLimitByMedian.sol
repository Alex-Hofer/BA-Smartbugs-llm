// mwevariety_fixed: aus Web3Bugs-Originalquellen geflattet (siehe corpus_tools/build_fixed.py)
// SPDX-License-Identifier: MIT
pragma solidity 0.8.36;

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\45@0.8\@openzeppelin\contracts\utils\math\Math.sol ----
// license-stripped



/**
 * @dev Standard math utilities missing in the Solidity language.
 */
library Math {
    /**
     * @dev Returns the largest of two numbers.
     */
    function max(uint256 a, uint256 b) internal pure returns (uint256) {
        return a >= b ? a : b;
    }

    /**
     * @dev Returns the smallest of two numbers.
     */
    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }

    /**
     * @dev Returns the average of two numbers. The result is rounded towards
     * zero.
     */
    function average(uint256 a, uint256 b) internal pure returns (uint256) {
        // (a + b) / 2 can overflow.
        return (a & b) + (a ^ b) / 2;
    }

    /**
     * @dev Returns the ceiling of the division of two numbers.
     *
     * This differs from standard division with `/` in that it rounds up instead
     * of rounding down.
     */
    function ceilDiv(uint256 a, uint256 b) internal pure returns (uint256) {
        // (a + b - 1) / b can overflow on addition, so we distribute.
        return a / b + (a % b == 0 ? 0 : 1);
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\45@0.8\@openzeppelin\contracts\utils\Context.sol ----
// license-stripped



/**
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\45@0.8\@openzeppelin\contracts\access\Ownable.sol ----
// license-stripped





/**
 * @dev Contract module which provides a basic access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * By default, the owner account will be the one that deploys the contract. This
 * can later be changed with {transferOwnership}.
 *
 * This module is used through inheritance. It will make available the modifier
 * `onlyOwner`, which can be applied to your functions to restrict their use to
 * the owner.
 */
abstract contract Ownable is Context {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Initializes the contract setting the deployer as the initial owner.
     */
    constructor() {
        _setOwner(_msgSender());
    }

    /**
     * @dev Returns the address of the current owner.
     */
    function owner() public view virtual returns (address) {
        return _owner;
    }

    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
        _;
    }

    /**
     * @dev Leaves the contract without owner. It will not be possible to call
     * `onlyOwner` functions anymore. Can only be called by the current owner.
     *
     * NOTE: Renouncing ownership will leave the contract without an owner,
     * thereby removing any functionality that is only available to the owner.
     */
    function renounceOwnership() public virtual onlyOwner {
        _setOwner(address(0));
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        _setOwner(newOwner);
    }

    function _setOwner(address newOwner) private {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}

// ---- 45\contracts\interfaces\ICreditLimitModel.sol ----
//license-stripped


/**
 * @title CreditLimitModel Interface
 *  @dev Calculate the user's credit line based on the trust he receives from the vouchees.
 */
interface ICreditLimitModel {
    struct LockedInfo {
        address staker;
        uint256 vouchingAmount;
        uint256 lockedAmount;
        uint256 availableStakingAmount;
    }

    function isCreditLimitModel() external pure returns (bool);

    function effectiveNumber() external returns (uint256);

    /**
     * @notice Calculates the staker locked amount
     * @return Member credit limit
     */
    function getLockedAmount(
        LockedInfo[] calldata vouchAmountList,
        address staker,
        uint256 amount,
        bool isIncrease
    ) external pure returns (uint256);

    /**
     * @notice Calculates the member credit limit by vouchs
     * @return Member credit limit
     */
    function getCreditLimit(uint256[] calldata vouchs) external view returns (uint256);
}

// ---- 45\contracts\user\CreditLimitByMedian.sol ----
//license-stripped







contract CreditLimitByMedian is Ownable, ICreditLimitModel {
    using Math for uint256;

    bool public constant override isCreditLimitModel = true;
    uint256 public override effectiveNumber;

    constructor(uint256 effectiveNumber_) {
        effectiveNumber = effectiveNumber_;
    }

    function getCreditLimit(uint256[] memory vouchs) public view override returns (uint256) {
        if (vouchs.length >= effectiveNumber) {
            return _findMedian(vouchs);
        } else {
            return 0;
        }
    }

    function getLockedAmount(
        LockedInfo[] memory array,
        address account,
        uint256 amount,
        bool isIncrease
    ) public pure override returns (uint256) {
        if (array.length == 0) return 0;

        uint256 newLockedAmount;
        if (isIncrease) {
            for (uint256 i = 0; i < array.length; i++) {
                uint256 remainingVouchingAmount;
                if (array[i].vouchingAmount > array[i].lockedAmount) {
                    remainingVouchingAmount = array[i].vouchingAmount - array[i].lockedAmount;
                } else {
                    remainingVouchingAmount = 0;
                }

                if (remainingVouchingAmount > array[i].availableStakingAmount) {
                    if (array[i].availableStakingAmount > amount) {
                        newLockedAmount = array[i].lockedAmount + amount;
                    } else {
                        newLockedAmount = array[i].lockedAmount + array[i].availableStakingAmount;
                    }
                } else {
                    if (remainingVouchingAmount > amount) {
                        newLockedAmount = array[i].lockedAmount + amount;
                    } else {
                        newLockedAmount = array[i].lockedAmount + remainingVouchingAmount;
                    }
                }

                if (account == array[i].staker) {
                    return newLockedAmount;
                }
            }
        } else {
            for (uint256 i = 0; i < array.length; i++) {
                if (array[i].lockedAmount > amount) {
                    newLockedAmount = array[i].lockedAmount - 1;
                } else {
                    newLockedAmount = 0;
                }

                if (account == array[i].staker) {
                    return newLockedAmount;
                }
            }
        }

        return 0;
    }

    function setEffectNumber(uint256 number) external onlyOwner {
        effectiveNumber = number;
    }

    /**
     *  @dev Find median from uint array
     *  @param array array
     *  @return uint256
     */
    function _findMedian(uint256[] memory array) private pure returns (uint256) {
        uint256[] memory arr = _sortArray(array);
        if (arr.length == 0) return 0;

        if (arr.length % 2 == 0) {
            uint256 num1 = arr[arr.length >> 1];
            uint256 num2 = arr[(arr.length >> 1) - 1];
            return num1.average(num2);
        } else {
            return arr[arr.length >> 1];
        }
    }

    /**
     *  @dev Sort uint array
     *  @param arr array
     *  @return uint256 array
     */
    function _sortArray(uint256[] memory arr) private pure returns (uint256[] memory) {
        uint256 length = arr.length;

        for (uint256 i = 0; i < length; i++) {
            for (uint256 j = i + 1; j < length; j++) {
                if (arr[i] < arr[j]) {
                    uint256 temp = arr[j];
                    arr[j] = arr[i];
                    arr[i] = temp;
                }
            }
        }

        return arr;
    }
}
