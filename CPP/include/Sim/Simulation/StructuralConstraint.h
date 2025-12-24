//////////////////////////////////////////////////////////////////////////////
//
// Copyright 2025 Autodesk, Inc. All rights reserved.
//
// Use of this software is subject to the terms of the Autodesk license
// agreement provided at the time of installation or download, or which
// otherwise accompanies this software.
//
//////////////////////////////////////////////////////////////////////////////

#pragma once
#include "SimAttribute.h"
#include "../SimTypeDefs.h"

// THIS CLASS WILL BE VISIBLE TO AN API CLIENT.
// THIS HEADER FILE WILL BE GENERATED FROM NIDL.
#include "../../Core/OSMacros.h"

#ifdef SIMXINTERFACE_EXPORTS
# ifdef __COMPILING_ADSK_SIM_STRUCTURALCONSTRAINT_CPP__
# define ADSK_SIM_STRUCTURALCONSTRAINT_API XI_EXPORT
# else
# define ADSK_SIM_STRUCTURALCONSTRAINT_API
# endif
#else
# define ADSK_SIM_STRUCTURALCONSTRAINT_API XI_IMPORT
#endif

namespace adsk { namespace core {
    class Vector3D;
}}
namespace adsk { namespace sim {
    class ConstraintMask;
}}

namespace adsk { namespace sim {

/// !!!!! Warning !!!!!
/// ! This is hidden and not officially supported
/// !!!!! Warning !!!!!
/// 
/// Object that represents a structural constraint.
class StructuralConstraint : public SimAttribute {
public:

    /// The type of constraint.
    ConstraintTypes type() const;
    bool type(ConstraintTypes value);

    /// The constraint mask determines from the values in the displacement or rotation
    /// vectors which ones are (in)significant.
    core::Ptr<ConstraintMask> mask() const;
    bool mask(const core::Ptr<ConstraintMask>& value);

    /// The prescribed displacements values.
    core::Ptr<core::Vector3D> displacements() const;
    bool displacements(const core::Ptr<core::Vector3D>& value);

    /// The prescribed rotations values of the constraint.
    core::Ptr<core::Vector3D> rotations() const;
    bool rotations(const core::Ptr<core::Vector3D>& value);

    ADSK_SIM_STRUCTURALCONSTRAINT_API static const char* classType();
    ADSK_SIM_STRUCTURALCONSTRAINT_API const char* objectType() const override;
    ADSK_SIM_STRUCTURALCONSTRAINT_API void* queryInterface(const char* id) const override;
    ADSK_SIM_STRUCTURALCONSTRAINT_API static const char* interfaceId() { return classType(); }

private:

    // Raw interface
    virtual ConstraintTypes type_raw() const = 0;
    virtual bool type_raw(ConstraintTypes value) = 0;
    virtual ConstraintMask* mask_raw() const = 0;
    virtual bool mask_raw(ConstraintMask* value) = 0;
    virtual core::Vector3D* displacements_raw() const = 0;
    virtual bool displacements_raw(core::Vector3D* value) = 0;
    virtual core::Vector3D* rotations_raw() const = 0;
    virtual bool rotations_raw(core::Vector3D* value) = 0;
    virtual void placeholderStructuralConstraint0() {}
    virtual void placeholderStructuralConstraint1() {}
    virtual void placeholderStructuralConstraint2() {}
    virtual void placeholderStructuralConstraint3() {}
    virtual void placeholderStructuralConstraint4() {}
    virtual void placeholderStructuralConstraint5() {}
    virtual void placeholderStructuralConstraint6() {}
    virtual void placeholderStructuralConstraint7() {}
    virtual void placeholderStructuralConstraint8() {}
    virtual void placeholderStructuralConstraint9() {}
    virtual void placeholderStructuralConstraint10() {}
    virtual void placeholderStructuralConstraint11() {}
    virtual void placeholderStructuralConstraint12() {}
    virtual void placeholderStructuralConstraint13() {}
    virtual void placeholderStructuralConstraint14() {}
    virtual void placeholderStructuralConstraint15() {}
    virtual void placeholderStructuralConstraint16() {}
    virtual void placeholderStructuralConstraint17() {}
    virtual void placeholderStructuralConstraint18() {}
    virtual void placeholderStructuralConstraint19() {}
    virtual void placeholderStructuralConstraint20() {}
    virtual void placeholderStructuralConstraint21() {}
    virtual void placeholderStructuralConstraint22() {}
    virtual void placeholderStructuralConstraint23() {}
};

// Inline wrappers

inline ConstraintTypes StructuralConstraint::type() const
{
    ConstraintTypes res = type_raw();
    return res;
}

inline bool StructuralConstraint::type(ConstraintTypes value)
{
    return type_raw(value);
}

inline core::Ptr<ConstraintMask> StructuralConstraint::mask() const
{
    core::Ptr<ConstraintMask> res = mask_raw();
    return res;
}

inline bool StructuralConstraint::mask(const core::Ptr<ConstraintMask>& value)
{
    return mask_raw(value.get());
}

inline core::Ptr<core::Vector3D> StructuralConstraint::displacements() const
{
    core::Ptr<core::Vector3D> res = displacements_raw();
    return res;
}

inline bool StructuralConstraint::displacements(const core::Ptr<core::Vector3D>& value)
{
    return displacements_raw(value.get());
}

inline core::Ptr<core::Vector3D> StructuralConstraint::rotations() const
{
    core::Ptr<core::Vector3D> res = rotations_raw();
    return res;
}

inline bool StructuralConstraint::rotations(const core::Ptr<core::Vector3D>& value)
{
    return rotations_raw(value.get());
}
}// namespace sim
}// namespace adsk

#undef ADSK_SIM_STRUCTURALCONSTRAINT_API